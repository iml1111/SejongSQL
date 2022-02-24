from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

OK = (
    lambda x: Response({'msg':'success'}, status=HTTP_200_OK)
    if x is None else
    Response({'msg': 'success', 'result': x}, status=HTTP_200_OK)
)

CREATED = (
    lambda x: Response({'msg':'created'}, status=HTTP_201_CREATED)
    if x is None else
    Response({'msg': 'created', 'result': x}, status=HTTP_201_CREATED)
)

NO_CONTENT = Response({}, status=HTTP_204_NO_CONTENT)

BAD_REQUEST = (
    lambda x: Response(
        {'msg': 'fail', 'description': x},
        status=HTTP_400_BAD_REQUEST
    )
)

UNAUTHORIZED = (
    lambda x: Response(
        {'msg': 'fail', 'description': x},
        status=HTTP_401_UNAUTHORIZED
    )
)

FORBIDDEN = (
    lambda x: Response(
        {'msg': 'fail', 'description': x},
        status=HTTP_403_FORBIDDEN
    )
)

NOT_FOUND = Response(
    {
        'msg': 'fail',
        'description': "Resource not found."
    },
    status=HTTP_404_NOT_FOUND,
)
