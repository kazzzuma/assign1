"""
Implementation of an SMC client.

MODIFY THIS FILE.
"""
# You might want to import more classes if needed.

import collections
import json
import pickle
from typing import (
    Dict,
    Set,
    Tuple,
    Union
)

from communication import Communication
from expression import (
    Expression,
    Secret, AbstractOperator, Addition, Substraction
)
from protocol import ProtocolSpec
from secret_sharing import(
    reconstruct_secret,
    share_secret,
    Share,
)

# Feel free to add as many imports as you want.


class SMCParty:
    """
    A client that executes an SMC protocol to collectively compute a value of an expression together
    with other clients.

    Attributes:
        client_id: Identifier of this client
        server_host: hostname of the server
        server_port: port of the server
        protocol_spec (ProtocolSpec): Protocol specification
        value_dict (dict): Dictionary assigning values to secrets belonging to this client.
    """

    # public message contains label imply that sending shares to others are finished
    SHARE_PUBLISH_LABEL = "_send_share_over"
    SHARE_PRIVATE_LABEL = "share_from_"
    BROADCAST_SHARE_LABEL = "_broadcast_share"

    def __init__(
            self,
            client_id: str,
            server_host: str,
            server_port: int,
            protocol_spec: ProtocolSpec,
            value_dict: Dict[Secret, int]
        ):
        self.comm = Communication(server_host, server_port, client_id)

        self.client_id = client_id
        self.protocol_spec = protocol_spec
        self.value_dict = value_dict
        self.client_name_idx_dict = dict()
        self.secret_share_dict = dict()


    def run(self) -> int:
        """
        The method the client use to do the SMC.
        """
        # 1. encryption and share
        self.create_and_send_share()

        # 2. wait until ensuring all others finish the process of encryption and then sharing
        self.check_share_complete()

        # 3. process expression
        curr_share = self.process_expression(self.protocol_spec.expr)

        complete_share_list = [curr_share]

        # 4. broadcast the processed expression
        self.broadcast_curr_share(curr_share)

        # 5. receive the result from other parties
        self.retrieve_broadcast_share(complete_share_list)

        # 6. call function reconstruction to get the final result
        return reconstruct_secret(complete_share_list)



    # Suggestion: To process expressions, make use of the *visitor pattern* like so:
    def process_expression(
            self,
            expr: Expression
        ) -> Share:
        if isinstance(expr, Secret):
            # get self's share, retrieve others' share
            return self.get_or_retrieve_share(expr)

        if isinstance(expr, AbstractOperator):
            pre_expr_share = self.process_expression(expr.pre_expr)
            next_expr_share = self.process_expression(expr.next_expr)
            if isinstance(expr, Addition):
                return pre_expr_share + next_expr_share
            elif isinstance(expr, Substraction):
                return pre_expr_share - next_expr_share
        # if expr is a multiplication operation:
        #     ...

        # if expr is a secret:
        #     ...

        # if expr is a scalar:
        #     ...
        #
        # Call specialized methods for each expression type, and have these specialized
        # methods in turn call `process_expression` on their sub-expressions to process
        # further.
        pass

    # Feel free to add as many methods as you want.
    def create_and_send_share(self) -> Share:
        # 1. get own value
        secret = next(iter(self.value_dict.keys()))
        value = next(iter(self.value_dict.values()))

        # 2. encrypt shares
        share_list = share_secret(value, len(self.protocol_spec.participant_ids))

        # 3. map client_name to client_idx
        for idx, client_name in enumerate(self.protocol_spec.participant_ids):
            self.client_name_idx_dict[client_name] = idx

        # 4. map secret to share
        self.secret_share_dict[secret.id] = share_list[self.client_name_idx_dict[self.client_id]]

        # 5. send encrypted shares to others
        for client_name in self.protocol_spec.participant_ids:
            if client_name != self.client_id:
                idx = self.client_name_idx_dict[client_name]
                share = share_list[idx]
                self.comm.send_private_message(client_name,
                                               self.SHARE_PRIVATE_LABEL + str(secret.id),
                                               pickle.dumps(share))

        # 6. inform all other parties that all shares are sent out
        self.comm.publish_message(self.client_id + self.SHARE_PUBLISH_LABEL, "~")

        # 7. return my own share
        return self.secret_share_dict[secret.id]

    def check_share_complete(self):
        for client_name in self.protocol_spec.participant_ids:
            if client_name != self.client_id:
                self.comm.retrieve_public_message(client_name, client_name + self.SHARE_PUBLISH_LABEL)

    def get_or_retrieve_share(self, secret) -> Share:
        # if the secret belongs to mine
        if secret.id in self.secret_share_dict:
            return self.secret_share_dict[secret.id]
        # if the secret belongs to other parties
        for client_name in self.protocol_spec.participant_ids:
            if client_name != self.client_id:
                self.secret_share_dict[secret.id] = pickle.loads(
                    self.comm.retrieve_private_message(
                        self.SHARE_PRIVATE_LABEL+str(secret.id)
                    )
                )
        return self.secret_share_dict[secret.id]

    def broadcast_curr_share(self, curr_share):
        """
        broadcast the result computed by myself
        """
        self.comm.publish_message(self.client_id+self.BROADCAST_SHARE_LABEL, pickle.dumps(curr_share))

    def retrieve_broadcast_share(self, complete_share_list):
        """
        receive the result computed by others
        """
        for client_name in self.protocol_spec.participant_ids:
            if client_name != self.client_id:
                complete_share_list.append(
                    pickle.loads(
                        self.comm.retrieve_public_message(
                            client_name, client_name+self.BROADCAST_SHARE_LABEL
                        )
                    )
                )


