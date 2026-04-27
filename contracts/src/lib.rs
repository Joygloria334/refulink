#![no_std]
use soroban_sdk::{
    contract, contractimpl, contracttype, symbol_short, Address, BytesN, Env, Symbol,
};

// ── Storage key enum ────────────────────────────────────────────────────────
// Using an enum avoids key collisions between different stored types.
#[contracttype]
enum DataKey {
    Vouch(Address),  // persistent: VouchRecord keyed by refugee Address
    Ambassador,      // instance:   the single trusted ambassador Address
    Initialized,     // instance:   one-time init guard
}

// ── On-chain vouch record ────────────────────────────────────────────────────
#[contracttype]
#[derive(Clone)]
pub struct VouchRecord {
    pub ambassador: Address,
    pub hashed_rin: BytesN<32>, // SHA-256 of the refugee's RIN — no PII on-chain
    pub vouched_at: u64,        // ledger timestamp at time of vouching
}

// ── Contract ────────────────────────────────────────────────────────────────
#[contract]
pub struct VouchContract;

#[contractimpl]
impl VouchContract {
    /// One-time initialisation. Sets the single trusted Ambassador address.
    /// Panics if called more than once.
    pub fn init(env: Env, ambassador: Address) {
        if env
            .storage()
            .instance()
            .has(&DataKey::Initialized)
        {
            panic!("already initialized");
        }
        env.storage()
            .instance()
            .set(&DataKey::Ambassador, &ambassador);
        env.storage()
            .instance()
            .set(&DataKey::Initialized, &true);
    }

    /// Ambassador signs an attestation for a refugee's Stellar public key.
    /// Requires the caller to be the pre-configured trusted Ambassador.
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

        // Keep the vouch record alive for ~1 year of ledgers (5-second ledgers).
        env.storage()
            .persistent()
            .extend_ttl(&DataKey::Vouch(target), 100, 6_307_200);
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
