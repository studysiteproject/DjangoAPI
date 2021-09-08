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
        return Response(serializer.data)       

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
            return Response(msg, status=status.HTTP_200_OK)

        serializer = BoardSerializer(board)
        return Response(serializer.data)   

# 게시글 생성에서 사용할 클래스
class BoardCreateView(APIView): 

    # def get(self, request, *args, **kwargs):
    #     context = {}
    #     return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        post_data = {key: request.POST.get(key) for key in ('title', 'content', 'author')}

        for key in post_data:
            if not post_data[key]:
                raise Http404('No Data For {}'.format(key))

        Board.objects.create(title=post_data['title'], content=post_data['content'], author=post_data['author'])

        msg = {'state': 'success'}
        return Response(msg, status=status.HTTP_200_OK)

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
            if not post_data[key]:
                raise Http404('No Data For {}'.format(key))
        
        board = self.get_object()

        if not board:
            msg = {'state': 'fail', 'detail': 'invalid board_id'}
            return Response(msg, status=status.HTTP_200_OK)
        
        for key, value in post_data.items():
            setattr(board, key, value)
        
        board.save()

        msg = {'state': 'success'}
        return Response(msg, status=status.HTTP_200_OK)

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
            return Response(msg, status=status.HTTP_200_OK)

        board.delete()

        msg = {'state': 'success'}
        return Response(msg, status=status.HTTP_200_OK)