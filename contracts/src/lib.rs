#![no_std]
use soroban_sdk::{
    contract, contractimpl, contracttype, Address, BytesN, Env,
};

// ── Storage key enum ────────────────────────────────────────────────────────
#[contracttype]
enum DataKey {
    Vouch(Address),    // persistent: VouchRecord keyed by refugee Address
    Identity(Address), // persistent: IdentityRecord keyed by refugee Address
    Ambassador,        // instance:   the single trusted ambassador Address
    Initialized,       // instance:   one-time init guard
}

// ── On-chain vouch record (social attestation) ───────────────────────────────
#[contracttype]
#[derive(Clone)]
pub struct VouchRecord {
    pub ambassador: Address,
    pub hashed_rin: BytesN<32>, // SHA-256 of the refugee's RIN — no PII on-chain
    pub vouched_at: u64,        // ledger timestamp at time of vouching
}

// ── On-chain identity record (registration + verified flag) ──────────────────
#[contracttype]
#[derive(Clone)]
pub struct IdentityRecord {
    pub hashed_rin: BytesN<32>, // SHA-256 of the refugee's RIN
    pub verified: bool,         // set to true after successful on-chain vouch
    pub registered_at: u64,     // ledger timestamp at registration
}

// ── Contract ─────────────────────────────────────────────────────────────────
#[contract]
pub struct VouchContract;

const TTL_THRESHOLD: u32 = 100;
const TTL_EXTEND: u32 = 6_307_200; // ~1 year at 5-second ledgers

#[contractimpl]
impl VouchContract {
    /// One-time initialisation. Sets the single trusted Ambassador address.
    pub fn init(env: Env, ambassador: Address) {
        if env.storage().instance().has(&DataKey::Initialized) {
            panic!("already initialized");
        }
        env.storage().instance().set(&DataKey::Ambassador, &ambassador);
        env.storage().instance().set(&DataKey::Initialized, &true);
    }

    // ── Identity registration ─────────────────────────────────────────────────

    /// Admin registers a refugee's hashed RIN linked to their Stellar address.
    /// Sets verified = false. Must be called by the trusted Ambassador.
    pub fn register_identity(env: Env, admin: Address, target: Address, hashed_rin: BytesN<32>) {
        admin.require_auth();
        let trusted: Address = env
            .storage()
            .instance()
            .get(&DataKey::Ambassador)
            .expect("not initialized");
        if admin != trusted {
            panic!("unauthorized");
        }

        let record = IdentityRecord {
            hashed_rin,
            verified: false,
            registered_at: env.ledger().timestamp(),
        };
        env.storage()
            .persistent()
            .set(&DataKey::Identity(target.clone()), &record);
        env.storage()
            .persistent()
            .extend_ttl(&DataKey::Identity(target), TTL_THRESHOLD, TTL_EXTEND);
    }

    /// Admin flips the verified flag for a registered refugee address.
    pub fn set_verified(env: Env, admin: Address, target: Address, verified: bool) {
        admin.require_auth();
        let trusted: Address = env
            .storage()
            .instance()
            .get(&DataKey::Ambassador)
            .expect("not initialized");
        if admin != trusted {
            panic!("unauthorized");
        }

        let mut record: IdentityRecord = env
            .storage()
            .persistent()
            .get(&DataKey::Identity(target.clone()))
            .expect("not registered");
        record.verified = verified;
        env.storage()
            .persistent()
            .set(&DataKey::Identity(target.clone()), &record);
        env.storage()
            .persistent()
            .extend_ttl(&DataKey::Identity(target), TTL_THRESHOLD, TTL_EXTEND);
    }

    /// Returns the verified flag for the given address. False if not registered.
    pub fn is_verified(env: Env, target: Address) -> bool {
        env.storage()
            .persistent()
            .get::<DataKey, IdentityRecord>(&DataKey::Identity(target))
            .map(|r| r.verified)
            .unwrap_or(false)
    }

    /// Returns the full IdentityRecord. Panics if address was never registered.
    pub fn get_identity(env: Env, target: Address) -> IdentityRecord {
        env.storage()
            .persistent()
            .get(&DataKey::Identity(target))
            .expect("not registered")
    }

    // ── Social vouching ───────────────────────────────────────────────────────

    /// Ambassador signs an attestation for a refugee's Stellar public key.
    pub fn vouch(env: Env, ambassador: Address, target: Address, hashed_rin: BytesN<32>) {
        ambassador.require_auth();
        let trusted: Address = env
            .storage()
            .instance()
            .get(&DataKey::Ambassador)
            .expect("not initialized");
        if ambassador != trusted {
            panic!("unauthorized: not the trusted ambassador");
        }

        let record = VouchRecord {
            ambassador,
            hashed_rin,
            vouched_at: env.ledger().timestamp(),
        };
        env.storage()
            .persistent()
            .set(&DataKey::Vouch(target.clone()), &record);
        env.storage()
            .persistent()
            .extend_ttl(&DataKey::Vouch(target), TTL_THRESHOLD, TTL_EXTEND);
    }

    /// Returns true if the given address has been vouched by the Ambassador.
    pub fn is_vouched(env: Env, target: Address) -> bool {
        env.storage()
            .persistent()
            .has(&DataKey::Vouch(target))
    }

    /// Returns the full VouchRecord for an address. Panics if not vouched.
    pub fn get_vouch(env: Env, target: Address) -> VouchRecord {
        env.storage()
            .persistent()
            .get(&DataKey::Vouch(target))
            .expect("not vouched")
    }
}

mod test;
