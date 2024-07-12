# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import pb.c2_pb2 as c2__pb2

GRPC_GENERATED_VERSION = '1.64.1'
GRPC_VERSION = grpc.__version__
EXPECTED_ERROR_RELEASE = '1.65.0'
SCHEDULED_RELEASE_DATE = 'June 25, 2024'
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    warnings.warn(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in c2_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
        + f' This warning will become an error in {EXPECTED_ERROR_RELEASE},'
        + f' scheduled for release on {SCHEDULED_RELEASE_DATE}.',
        RuntimeWarning
    )


class C2Stub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Hello = channel.unary_unary(
                '/c2.C2/Hello',
                request_serializer=c2__pb2.HelloReq.SerializeToString,
                response_deserializer=c2__pb2.HelloRes.FromString,
                _registered_method=True)
        self.Eradicate = channel.unary_unary(
                '/c2.C2/Eradicate',
                request_serializer=c2__pb2.EradicateReq.SerializeToString,
                response_deserializer=c2__pb2.EradicateRes.FromString,
                _registered_method=True)
        self.PushActions = channel.unary_unary(
                '/c2.C2/PushActions',
                request_serializer=c2__pb2.PushActionsReq.SerializeToString,
                response_deserializer=c2__pb2.PushActionsRes.FromString,
                _registered_method=True)
        self.GetPositions = channel.unary_unary(
                '/c2.C2/GetPositions',
                request_serializer=c2__pb2.GetPositionsReq.SerializeToString,
                response_deserializer=c2__pb2.GetPositionsRes.FromString,
                _registered_method=True)


class C2Servicer(object):
    """Missing associated documentation comment in .proto file."""

    def Hello(self, request, context):
        """simple hello to check connection
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Eradicate(self, request, context):
        """reset everything to default
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def PushActions(self, request, context):
        """tells the server to perform the given actions
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetPositions(self, request, context):
        """gets the attacker positions since the last time this endpoint was queried
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_C2Servicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Hello': grpc.unary_unary_rpc_method_handler(
                    servicer.Hello,
                    request_deserializer=c2__pb2.HelloReq.FromString,
                    response_serializer=c2__pb2.HelloRes.SerializeToString,
            ),
            'Eradicate': grpc.unary_unary_rpc_method_handler(
                    servicer.Eradicate,
                    request_deserializer=c2__pb2.EradicateReq.FromString,
                    response_serializer=c2__pb2.EradicateRes.SerializeToString,
            ),
            'PushActions': grpc.unary_unary_rpc_method_handler(
                    servicer.PushActions,
                    request_deserializer=c2__pb2.PushActionsReq.FromString,
                    response_serializer=c2__pb2.PushActionsRes.SerializeToString,
            ),
            'GetPositions': grpc.unary_unary_rpc_method_handler(
                    servicer.GetPositions,
                    request_deserializer=c2__pb2.GetPositionsReq.FromString,
                    response_serializer=c2__pb2.GetPositionsRes.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'c2.C2', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('c2.C2', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class C2(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Hello(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/c2.C2/Hello',
            c2__pb2.HelloReq.SerializeToString,
            c2__pb2.HelloRes.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Eradicate(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/c2.C2/Eradicate',
            c2__pb2.EradicateReq.SerializeToString,
            c2__pb2.EradicateRes.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def PushActions(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/c2.C2/PushActions',
            c2__pb2.PushActionsReq.SerializeToString,
            c2__pb2.PushActionsRes.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetPositions(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/c2.C2/GetPositions',
            c2__pb2.GetPositionsReq.SerializeToString,
            c2__pb2.GetPositionsRes.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
