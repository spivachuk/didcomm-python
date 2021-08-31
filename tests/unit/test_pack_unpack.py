import pytest
from authlib.common.encoding import json_dumps, to_bytes, urlsafe_b64decode, to_unicode, json_loads

from didcomm.common.resolvers import ResolversConfig
from didcomm.common.types import VerificationMethodType, VerificationMaterial, VerificationMaterialFormat
from didcomm.did_doc.did_doc import VerificationMethod
from didcomm.message import Message
from didcomm.pack_signed import pack_signed
from didcomm.secrets.secrets_resolver import Secret
from tests.common.example_resolvers import ExampleSecretsResolver, ExampleDIDResolver, ExampleDIDDoc


@pytest.mark.asyncio
async def test_pack_signed():
    alice_secret = Secret(
        kid="did:example:alice#key-1",
        type=VerificationMethodType.ED25519_VERIFICATION_KEY_2018,
        verification_material=VerificationMaterial(
            format=VerificationMaterialFormat.JWK,
            value=json_dumps({
                "kty": "OKP",
                "d": "uuAE6HmqnCnVjkF0ygjZMQiHeYIvI3Qcwh_2SjGMG-o",
                "crv": "Ed25519",
                "x": "z0x6oKBZ-ehwn_tkBzbhav132eQ7vmj5s5Xen00rtW0"
            })
        )
    )

    secrets_resolver = ExampleSecretsResolver([alice_secret])

    alice_did_doc = ExampleDIDDoc(
        did="did:example:alice",
        key_agreement_kids=[],
        authentication_kids=["did:example:alice#key-1"],
        verification_methods=[VerificationMethod(
            id="did:example:alice#key-1",
            type=VerificationMethodType.ED25519_VERIFICATION_KEY_2018,
            controller="did:example:alice",
            verification_material=VerificationMaterial(
                format=VerificationMaterialFormat.JWK,
                value=json_dumps({
                    "kty": "OKP",
                    "crv": "Ed25519",
                    "x": "z0x6oKBZ-ehwn_tkBzbhav132eQ7vmj5s5Xen00rtW0"
                })
            )
        )],
        didcomm_services=[]
    )

    did_resolver = ExampleDIDResolver([alice_did_doc])

    message = Message(
        id="1234567890",
        typ="application/didcomm-plain+json",
        type="http://example.com/protocols/lets_do_lunch/1.0/proposal",
        frm="did:example:alice",
        to=[
            "did:example:bob",
            "did:example:charlie"
        ],
        created_time=1516269022,
        expires_time=1516385931,
        body={
            "messagespecificattribute": "and its value"
        }
    )

    resolvers_config = ResolversConfig(secrets_resolver, did_resolver)

    result = await pack_signed(message, "did:example:alice", resolvers_config)

    actual_decoded_packed_msg_wo_signature = _encode_and_remove_signatures(result.packed_msg)

    expected_packed_msg = json_dumps({
        "payload": "eyJpZCI6IjEyMzQ1Njc4OTAiLCJ0eXAiOiJhcHBsaWNhdGlvbi9kaWRjb21tLXBsYWluK2pzb24iLCJ0" +
                   "eXBlIjoiaHR0cDovL2V4YW1wbGUuY29tL3Byb3RvY29scy9sZXRzX2RvX2x1bmNoLzEuMC9wcm9wb3Nh" +
                   "bCIsImZyb20iOiJkaWQ6ZXhhbXBsZTphbGljZSIsInRvIjpbImRpZDpleGFtcGxlOmJvYiIsImRpZDpl" +
                   "eGFtcGxlOmNoYXJsaWUiXSwiY3JlYXRlZF90aW1lIjoiMTUxNjI2OTAyMiIsImV4cGlyZXNfdGltZSI6" +
                   "IjE1MTYzODU5MzEiLCJib2R5Ijp7Im1lc3NhZ2VzcGVjaWZpY2F0dHJpYnV0ZSI6ImFuZCBpdHMgdmFs" +
                   "dWUifX0",
        "signatures": [
            {
                "protected": "eyJ0eXAiOiJhcHBsaWNhdGlvbi9kaWRjb21tLXNpZ25lZCtqc29uIiwiYWxnIjoiRWREU0EifQ",
                "signature": "c26FsvxGqpZcpyFYFWnxxPHP1eGQwi2PtVzHPdH-ZtIY334OLjefbKLmVvQC9eWkQzy8DiD5yfrb0L1dkkBQDg",
                "header": {
                    "kid": "did:example:alice#key-1"
                }
            }
        ]
    })
    expected_decoded_packed_msg_wo_signature = _encode_and_remove_signatures(expected_packed_msg)

    expected_sign_from_kid = "did:example:alice#key-1"

    assert actual_decoded_packed_msg_wo_signature == expected_decoded_packed_msg_wo_signature
    assert result.sign_from_kid == expected_sign_from_kid


def _parse_base64url_encoded_json(base64url):
    return json_loads(to_unicode(urlsafe_b64decode(to_bytes(base64url))))


def _encode_and_remove_signatures(jws: str) -> dict:
    jws = json_loads(jws)
    jws['payload'] = _parse_base64url_encoded_json(jws['payload'])
    for s in jws['signatures']:
        s['protected'] = _parse_base64url_encoded_json(s['protected'])
        del s['signature']