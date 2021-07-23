import pytest as pytest

from didcomm.pack import PackBuilder
from didcomm.types.algorithms import EncAlgAnonCrypt
from didcomm.types.message import Message
from didcomm.types.mtc import MTC
from didcomm.unpack import Unpacker
from tests.common.interfaces_test import TestSecretsResolver, TestDIDResolver

ALICE_DID = "did:example:alice"
BOB_DID = "did:example:bob"
CAROL_DID = "did:example:carol"


@pytest.mark.asyncio
async def test_demo_anoncrypt_authcrypt_signed():
    # ALICE
    payload = {"aaa": 1, "bbb": 2}
    msg = Message(payload=payload, id="1234567890", type="my-protocol/1.0",
                  frm=ALICE_DID, to=[BOB_DID, CAROL_DID],
                  created_time=1516269022, expires_time=1516385931,
                  typ="application/didcomm-plain+json")
    packed_msg = await PackBuilder() \
        .did_resolver(TestDIDResolver()) \
        .secrets_resolver(TestSecretsResolver()) \
        .sign(from_did=ALICE_DID) \
        .auth_crypt(from_did=ALICE_DID, to_dids=[BOB_DID, CAROL_DID]) \
        .anon_crypt(to_dids=[BOB_DID, CAROL_DID], enc=EncAlgAnonCrypt.XC20P) \
        .finalize() \
        .pack(msg)

    # BOB
    unpack_result_bob = await Unpacker(
        is_forward=False, mtc=MTC(),
        did_resolver=TestDIDResolver(), secrets_resolver=TestSecretsResolver()
    ).unpack(packed_msg)

    # CAROL
    unpack_result_carol = await Unpacker(
        is_forward=False, mtc=MTC(),
        did_resolver=TestDIDResolver(), secrets_resolver=TestSecretsResolver()
    ).unpack(packed_msg)
