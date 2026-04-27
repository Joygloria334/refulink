#![cfg(test)]

use super::*;
use soroban_sdk::testutils::Address as _;
use soroban_sdk::{BytesN, Env};

fn setup() -> (Env, VouchContractClient<'static>, Address) {
    let env = Env::default();
    env.mock_all_auths();
    let contract_id = env.register_contract(None, VouchContract);
    let client = VouchContractClient::new(&env, &contract_id);
    let ambassador = Address::generate(&env);
    client.init(&ambassador);
    (env, client, ambassador)
}

#[test]
fn test_vouch_flow() {
    let (env, client, ambassador) = setup();
    let refugee = Address::generate(&env);
    let hashed_rin: BytesN<32> = BytesN::from_array(&env, &[0xabu8; 32]);

    assert!(!client.is_vouched(&refugee));

    client.vouch(&ambassador, &refugee, &hashed_rin);

    assert!(client.is_vouched(&refugee));

    let record = client.get_vouch(&refugee);
    assert_eq!(record.ambassador, ambassador);
    assert_eq!(record.hashed_rin, hashed_rin);
}

#[test]
#[should_panic(expected = "unauthorized")]
fn test_unauthorized_vouch_panics() {
    let (env, client, _ambassador) = setup();
    let impostor = Address::generate(&env);
    let refugee = Address::generate(&env);
    let hashed_rin: BytesN<32> = BytesN::from_array(&env, &[1u8; 32]);

    client.vouch(&impostor, &refugee, &hashed_rin);
}

#[test]
#[should_panic(expected = "already initialized")]
fn test_double_init_panics() {
    let (env, client, _) = setup();
    let second = Address::generate(&env);
    client.init(&second);
}

#[test]
#[should_panic(expected = "not vouched")]
fn test_get_vouch_not_found_panics() {
    let (env, client, _) = setup();
    let stranger = Address::generate(&env);
    client.get_vouch(&stranger);
}

#[test]
fn test_vouch_is_overwritable() {
    let (env, client, ambassador) = setup();
    let refugee = Address::generate(&env);
    let rin_v1: BytesN<32> = BytesN::from_array(&env, &[0x01u8; 32]);
    let rin_v2: BytesN<32> = BytesN::from_array(&env, &[0x02u8; 32]);

    client.vouch(&ambassador, &refugee, &rin_v1);
    client.vouch(&ambassador, &refugee, &rin_v2);

    let record = client.get_vouch(&refugee);
    assert_eq!(record.hashed_rin, rin_v2);
}
