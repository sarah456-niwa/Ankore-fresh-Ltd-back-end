from urllib.parse import parse_qs
import logging

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model

from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger(__name__)


class JWTAuthMiddleware:
    """Custom ASGI middleware that authenticates JWT tokens passed via query string.

    It expects the token as `?token=<JWT>` in the websocket URL.
    """

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return JWTAuthMiddlewareInstance(scope, self.inner)


class JWTAuthMiddlewareInstance:
    def __init__(self, scope, inner):
        self.scope = dict(scope)
        self.inner = inner

    async def __call__(self, receive, send):
        # Default to anonymous
        user = AnonymousUser()

        try:
            # Parse query string and look for token
            query_string = self.scope.get('query_string', b'').decode()
            qs = parse_qs(query_string)
            token_list = qs.get('token') or qs.get('access_token') or []
            if token_list:
                raw_token = token_list[0]
                # Remove Bearer prefix if present
                if raw_token.startswith('Bearer '):
                    raw_token = raw_token.split(' ', 1)[1]

                try:
                    # Validate token
                    validated = UntypedToken(raw_token)
                    # Extract user id from token payload
                    # Note: simplejwt stores user_id in token['user_id']
                    from jwt import decode as jwt_decode
                    from django.conf import settings

                    payload = jwt_decode(raw_token, settings.SECRET_KEY, algorithms=[settings.SIMPLE_JWT.get('ALGORITHM', 'HS256')])
                    user_id = payload.get('user_id') or payload.get('user') or payload.get('id')
                    User = get_user_model()
                    try:
                        user = await self._get_user(User, user_id)
                    except Exception:
                        user = AnonymousUser()
                except (InvalidToken, TokenError, Exception) as e:
                    logger.debug(f'Invalid websocket JWT token: {e}')
        except Exception as e:
            logger.debug(f'Error parsing websocket token: {e}')

        self.scope['user'] = user
        inner = self.inner(self.scope)
        return await inner(receive, send)

    @staticmethod
    async def _get_user(UserModel, user_id):
        # Import ORM inside function to avoid sync issues
        from asgiref.sync import sync_to_async

        @sync_to_async
        def get_user():
            return UserModel.objects.get(id=user_id)

        return await get_user()
