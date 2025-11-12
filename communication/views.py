from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .serializers import PixMessageSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import PixMessage
from datetime import datetime,  timezone
from faker import Faker
import random
import uuid

# Initialize Faker for Brazilian Portuguese data
fake = Faker('pt_BR')

@method_decorator(csrf_exempt, name='dispatch')
class PixMessageView(APIView):
  
  def post(self, request, ispb, number):
    try:
      number = int(number)

      if number <= 0:
        return Response({'error': 'Number parameter must be a positive integer.'}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
      return Response({'error': 'Number parameter must be provided.'}, status=status.HTTP_400_BAD_REQUEST)
    
    messages = []
    for _ in range(number):
      pagador_ispb = str(random.randint(10000000, 99999999))
      valor = round(random.uniform(1.00, 1000.00), 2)

      pagador = {
        "nome": fake.name(),
        "cpfCnpj": fake.cpf(),
        "ispb": pagador_ispb,
        "agencia": fake.random_number(digits=4, fix_len=True),
        "contaTransacional": fake.random_number(digits=6, fix_len=True),
        "tipoConta": random.choice(["CACC", "SVGS"])
      }

      recebedor = {
        "nome": fake.name(),
        "cpfCnpj": fake.cpf(),
        "ispb": ispb,
        "agencia": fake.random_number(digits=4, fix_len=True),
        "contaTransacional": fake.random_number(digits=6, fix_len=True),
        "tipoConta": random.choice(["CACC", "SVGS"])
      }

      message = PixMessage.objects.create(
        endToEndId=f"E{ispb}{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}{uuid.uuid4().hex[:6]}",
        pagador=pagador,
        recebedor=recebedor,
        valor=valor,
        dataHoraPagamento=datetime.now(),
        campoLivre="",
        txId=fake.uuid4(),
      )

      messages.append(message)

    serializer = PixMessageSerializer(messages, many=True)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
