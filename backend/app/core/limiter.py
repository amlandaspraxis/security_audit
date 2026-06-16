from slowapi import Limiter
from slowapi.util import get_remote_address

# Configure rate limiter using client's IP address
limiter = Limiter(key_func=get_remote_address)
