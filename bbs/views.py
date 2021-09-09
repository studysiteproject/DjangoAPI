from rest_framework import serializers, status
from rest_framework import response
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView

from .models import Board
from .serializers import BoardSerializer
from django.http import Http404

# Create your views here.
@api_view(['GET'])
def helloAPI(request):
    return Response("hello world")

# 게시글 리스트 확인 페이지에서 사용할 클래스
class BoardListView(APIView):

    queryset = Board.objects.all()

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.queryset

        queryset = Board.objects.all()
        
        return queryset

    def get(self, request, *args, **kwargs):

        # 해당 모델의 전체 데이터 얻어오기
        boards = self.get_object()

        serializer = BoardSerializer(boards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)       

# 게시글 상세 페이지에서 사용할 클래스
class BoardDetailView(APIView):

    queryset = Board.objects.all()
    pk_url_kwargs = 'board_id'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.queryset

        pk = self.kwargs.get(self.pk_url_kwargs)
        
        return queryset.filter(pk=pk).first()

    def get(self, request, *args, **kwargs):
        board = self.get_object()

        if not board:
            msg = {'state': 'fail', 'detail': 'invalid board_id'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        serializer = BoardSerializer(board)
        return Response(serializer.data, status=status.HTTP_200_OK)   

# 게시글 생성에서 사용할 클래스
class BoardCreateView(APIView): 

    # def get(self, request, *args, **kwargs):
    #     context = {}
    #     return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        post_data = {key: request.POST.get(key) for key in ('title', 'content', 'author')}

        for key in post_data:
            
            # 입력된 데이터가 존재하지 않을 때
            if not post_data[key]:
                msg = {'state': 'fail', 'detail': 'No Data For {}'.format(key)}
                return Response(msg, status=status.HTTP_400_BAD_REQUEST)
            
            # 입력된 데이터가 해당 필드의 제한 길이보다 긴 데이터일 때
            if Board._meta.get_field(key).max_length != None:
                if len(post_data[key]) < Board._meta.get_field(key).max_length:
                    msg = {'state': 'fail', 'detail': 'input over max length of {}'.format(key)}
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        Board.objects.create(title=post_data['title'], content=post_data['content'], author=post_data['author'])

        msg = {'state': 'success'}
        return Response(msg, status=status.HTTP_201_CREATED)

# 게시글 수정에서 사용할 클래스
class BoardUpdateView(APIView):

    queryset = Board.objects.all()
    pk_url_kwargs = 'board_id'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.queryset

        pk = self.kwargs.get(self.pk_url_kwargs)
        
        return queryset.filter(pk=pk).first()

    def post(self, request, *args, **kwargs):
        post_data = {key: request.POST.get(key) for key in ('title', 'content', 'author')}

        for key in post_data:

            # 입력된 데이터가 존재하지 않을 때
            if not post_data[key]:
                msg = {'state': 'fail', 'detail': 'No Data For {}'.format(key)}
                return Response(msg, status=status.HTTP_400_BAD_REQUEST)
            
            # 입력된 데이터가 해당 필드의 제한 길이보다 긴 데이터일 때
            if Board._meta.get_field(key).max_length != None:
                if len(post_data[key]) < Board._meta.get_field(key).max_length:
                    msg = {'state': 'fail', 'detail': 'input over max length of {}'.format(key)}
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        board = self.get_object()

        if not board:
            msg = {'state': 'fail', 'detail': 'invalid board_id'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        for key, value in post_data.items():
            setattr(board, key, value)
        
        board.save()

        msg = {'state': 'success'}
        return Response(msg, status=status.HTTP_201_CREATED)

# 게시글 삭제에서 사용할 클래스
class BoardDeleteView(APIView):

    queryset = Board.objects.all()
    pk_url_kwargs = 'board_id'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.queryset

        pk = self.kwargs.get(self.pk_url_kwargs)
        
        return queryset.filter(pk=pk).first()

    def get(self, request, *args, **kwargs):

        board = self.get_object()

        if not board:
            msg = {'state': 'fail', 'detail': 'invalid board_id'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        board.delete()

        msg = {'state': 'success'}
        return Response(msg, status=status.HTTP_200_OK)