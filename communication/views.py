from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.renderers import JSONRenderer
from .serializers import PixMessageSerializer
from rest_framework.response import Response
from .models import PixMessage, PixStream
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from datetime import datetime,  timezone
from django.http import JsonResponse
from rest_framework import status
from faker import Faker
import random
import uuid

# Classe para gerar mensagens Pix com dados falsos.
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

# Renderizador que aceita qualquer tipo de Header e evita o erro 406 (Not Acceptable) ao enviar um Header Accept multipart/json.
class FallbackJSONRenderer(JSONRenderer):
    media_type = '*/*'

class PixStreamStartView(APIView):
  renderer_classes = [FallbackJSONRenderer]

  def get(self, request, ispb):
    header = request.headers.get('Accept', 'application/json')
    multiple = header == 'multipart/json'
    
    # Busca todas as mensagens não visualizadas.
    all_receiver_messages = PixMessage.objects.filter(recebedor__ispb=ispb, visualizado=False)
  
    # Restringe o número de mensagens (10 no máximo) retornadas com base no cabeçalho Accept enviado.
    filtered_receiver_messages = list(all_receiver_messages[:10 if multiple else 1])

    # Se não houver mensagens, retorna 204 No Content.
    if not all_receiver_messages:
      return Response(status=status.HTTP_204_NO_CONTENT)
    
    # Marca as mensagens como visualizadas para não serem mais retornadas.
    all_receiver_messages \
      .filter(id__in=[msg.id for msg in filtered_receiver_messages]) \
      .update(visualizado=True)
    
    # Cria uma nova sessão de stream.
    stream_session = PixStream.objects.create(ispb=ispb)

    # Forma o link Pull-Next para ser retornado.
    pull_next = f"/api/pix/{ispb}/stream/{stream_session.id}"

    return _find_session_and_get_response_api(multiple, filtered_receiver_messages, pull_next)

  
class PixStreamNextView(APIView):
  renderer_classes = [FallbackJSONRenderer]

  def get(self, request, ispb, interationId):
    stream_session = PixStream.objects.filter(id=interationId, ispb=ispb).first()
    if not stream_session:
      return Response({'error': 'Stream session not found.'}, status=status.HTTP_404_NOT_FOUND)

    header = request.headers.get('Accept', 'application/json')
    multiple = header == 'multipart/json'
    
    # Busca todas as mensagens não visualizadas.
    all_receiver_messages = PixMessage.objects.filter(recebedor__ispb=ispb, visualizado=False)

    # Se não houver mensagens, retorna 204 No Content.
    if len(all_receiver_messages) == 0:
      return Response(status=status.HTTP_204_NO_CONTENT)
  
    # Restringe o número de mensagens (10 no máximo) retornadas com base no cabeçalho Accept enviado.
    filtered_receiver_messages = list(all_receiver_messages[:10 if multiple else 1])
    
    # Marca as mensagens como visualizadas para não serem mais retornadas.
    all_receiver_messages \
      .filter(id__in=[msg.id for msg in filtered_receiver_messages]) \
      .update(visualizado=True)
    
    # Forma o link Pull-Next para ser retornado.
    pull_next = f"/api/pix/{ispb}/stream/{stream_session.id}"

    return _find_session_and_get_response_api(multiple, filtered_receiver_messages, pull_next)

def _find_session_and_get_response_api(multiple, filtered_receiver_messages, pull_next):
  serializer = PixMessageSerializer(filtered_receiver_messages, many=True)
  
  # Retorna uma única mensagem com o cabeçalho Pull-Next.
  if not multiple:
    response = Response(serializer.data[0], content_type='application/json', status=status.HTTP_200_OK)
    response["Pull-Next"] = pull_next
    return response
  
  # Retorna múltiplas mensagens com o cabeçalho Pull-Next.
  response = JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)
  response["Pull-Next"] = pull_next

  return response