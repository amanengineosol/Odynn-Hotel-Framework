from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from gatekeeper.models.company_info import Company
import logging
logger = logging.getLogger(__name__)

class ClientAuthentication(BaseAuthentication):
   

    def authenticate(self, request):
        logger.info("Authenticating request using ClientAuthentication")
        company = request.data.get('client_id')
        if not company:
            return logger.error("No client id found")
        try:
            customer = Company.objects.get(uuid=company)
        except customer.DoesNotExist:
            raise AuthenticationFailed('No customer with this uuid found.')

        return (customer, None)  
