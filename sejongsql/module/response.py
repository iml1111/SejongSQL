from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

def OK(result=None):
    if result is None:
        return Response(
            {'msg':'success'},
            status=HTTP_200_OK
        )
    return Response(
        {'msg': 'success', 'result': result},
        status=HTTP_200_OK
    )


def CREATED(result=None):
    if result is None:
        return Response(
            {'msg': 'created'},
            status=HTTP_201_CREATED
        )
    return Response(
        {'msg': 'created', 'result': result},
        status=HTTP_201_CREATED
    )

NO_CONTENT = Response({}, status=HTTP_204_NO_CONTENT)

BAD_REQUEST = (
    lambda desc: Response(
        {
            'msg': 'fail',
            'error_code': 'bad_request',
            'description': desc
        },
        status=HTTP_400_BAD_REQUEST
    )
)

UNAUTHORIZED = (
    lambda desc: Response(
        {
            'msg': 'fail',
            'error_code': 'unauthorized',
            'description': desc
        },
        status=HTTP_401_UNAUTHORIZED
    )
)

FORBIDDEN = (
    lambda desc: Response(
        {
            'msg': 'fail',
            'error_code': 'forbidden',
            'description': desc
        },
        status=HTTP_403_FORBIDDEN
    )
)

NOT_FOUND = Response(
    {
        'msg': 'fail',
        'error_code': 'not_found',
        'description': "Resource not found."
    },
    status=HTTP_404_NOT_FOUND,
)

CONFLICT = (
    lambda desc: Response(
        {
            'msg': 'fail',
            'error_code': 'conflict',
            'description': desc
        },
        status = HTTP_409_CONFLICT
    )
)