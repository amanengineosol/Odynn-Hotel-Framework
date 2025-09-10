from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from gatekeeper.models.company_info import Company
import logging
logger = logging.getLogger(__name__)

class ClientAuthentication(BaseAuthentication):
   

    def authenticate(self, request):
        logger.info("Authenticating request..")
        company = request.data.get('client_id')
        if not company:
            return logger.error("No client id found")
        try:
            customer = Company.objects.get(uuid=company)
        except Company.DoesNotExist:
            logger.warning(f"User with this cloud id does not exist in db")
            raise AuthenticationFailed(detail="Wrong UUID provided. Please check your client id.")
        except ValidationError:
            raise AuthenticationFailed(detail="Wrong UUID provided. Please check your client id.")
        return (customer, None)
