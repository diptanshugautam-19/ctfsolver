#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <coroutine>

using u64 = uint64_t;
using u128 = unsigned __int128;

static void out(const std::string& s) {
    fwrite(s.data(), 1, s.size(), stdout);
    fflush(stdout);
}

static std::string read_line() {
    std::string s;
    int c;
    while ((c = getchar()) != EOF) {
        if (c == '\n') break;
        s.push_back((char)c);
        if (s.size() > 4096) break;
    }
    return s;
}

static int hexval(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static std::vector<uint8_t> from_hex(const std::string& s) {
    std::vector<uint8_t> v;
    std::string t;
    for (char c : s) if (hexval(c) >= 0) t.push_back(c);
    if (t.size() & 1) t.insert(t.begin(), '0');
    for (size_t i = 0; i + 1 < t.size(); i += 2) {
        v.push_back((uint8_t)((hexval(t[i]) << 4) | hexval(t[i + 1])));
    }
    return v;
}

static std::string to_hex(const std::vector<uint8_t>& v) {
    static const char* d = "0123456789abcdef";
    std::string s;
    for (uint8_t b : v) { s.push_back(d[b >> 4]); s.push_back(d[b & 15]); }
    return s;
}

static std::string u128_hex(u128 x) {
    if (x == 0) return "0";
    char buf[40];
    int i = 40;
    while (x) { int nyb = (int)(x & 15); buf[--i] = "0123456789abcdef"[nyb]; x >>= 4; }
    return std::string(buf + i, buf + 40);
}

static u128 hex_to_u128(const std::string& s) {
    u128 x = 0;
    for (char c : s) { int h = hexval(c); if (h < 0) continue; x = (x << 4) | (u128)h; }
    return x;
}

struct BigInt {
    u64 limbs[6];
    uint32_t len;
    bool neg;
};

struct KeyMaterial {
    BigInt p;
    BigInt q;
    BigInt e;
    BigInt n;
    BigInt d;
    u64 tag;
};

struct Msg {
    std::vector<uint8_t> data;
};

struct Signer {
    virtual void run(Msg& m) = 0;
};

struct Notary : Signer {
    u64 slot[6];
    Notary() {
        slot[0] = 0; slot[1] = 0; slot[2] = 0; slot[3] = 0; slot[4] = 0;
        slot[5] = 1;
    }
    void run(Msg& m) override;
};

struct EscrowAudit : Notary {
    void run(Msg& m) override;
};

void Notary::run(Msg& m) {
    out("receipt " + to_hex(m.data) + "\n");
}

void EscrowAudit::run(Msg& m) {
    const char* f = getenv("FLAG");
    std::string flag = f ? std::string(f) : std::string();
    std::vector<uint8_t> res(flag.size());
    for (size_t i = 0; i < flag.size(); i++) {
        uint8_t k = (i < m.data.size()) ? m.data[i] : 0;
        res[i] = (uint8_t)flag[i] ^ k;
    }
    out("audit " + to_hex(res) + "\n");
}

static constexpr size_t CELL = 320;
static constexpr size_t CELLS = 64;

struct Slab {
    alignas(16) uint8_t mem[CELL * CELLS];
    void* freelist[CELLS];
    size_t top;
    Slab() {
        top = 0;
        for (size_t i = 0; i < CELLS; i++) freelist[top++] = &mem[i * CELL];
    }
    void* alloc() {
        if (top == 0) return nullptr;
        return freelist[--top];
    }
    void release(void* p) {
        if (top < CELLS) freelist[top++] = p;
    }
};

static Slab g_slab;

static u128 load_u128(const BigInt& b) {
    return (u128)b.limbs[0] | ((u128)b.limbs[1] << 64);
}

static void store_u128(BigInt& b, u128 v) {
    b.limbs[0] = (u64)v;
    b.limbs[1] = (u64)(v >> 64);
    b.len = (v >> 64) ? 2 : 1;
    b.neg = false;
}

static void set_bigint(BigInt& b, const std::vector<uint8_t>& be) {
    memset(&b, 0, sizeof(b));
    u128 v = 0;
    for (uint8_t x : be) v = (v << 8) | x;
    store_u128(b, v);
}

static u128 gcd_u(u128 a, u128 b) {
    while (b) { u128 t = a % b; a = b; b = t; }
    return a;
}

static u128 mod_inv(u128 a, u128 m) {
    if (m <= 1) return 0;
    a %= m;
    __int128 old_r = (__int128)a, r = (__int128)m;
    __int128 old_s = 1, s = 0;
    while (r != 0) {
        __int128 q = old_r / r;
        __int128 t = old_r - q * r; old_r = r; r = t;
        t = old_s - q * s; old_s = s; s = t;
    }
    if (old_r != 1) return 0;
    __int128 res = old_s % (__int128)m;
    if (res < 0) res += (__int128)m;
    return (u128)res;
}

static u128 lcm_u(u128 a, u128 b) {
    if (a == 0 || b == 0) return 0;
    return a / gcd_u(a, b) * b;
}

struct Session;

struct DocAwaiter {
    Session* s;
    bool await_ready() const noexcept { return false; }
    void await_suspend(std::coroutine_handle<> h) noexcept;
    Msg await_resume() const noexcept;
};

struct Task {
    struct promise_type {
        Task get_return_object() {
            return Task{std::coroutine_handle<promise_type>::from_promise(*this)};
        }
        std::suspend_never initial_suspend() noexcept { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        void return_void() noexcept {}
        void unhandled_exception() noexcept { abort(); }
    };
    std::coroutine_handle<promise_type> h;
};

struct Session {
    std::coroutine_handle<Task::promise_type> frame{};
    bool armed = false;
    Msg doc;
    Signer* signer = nullptr;
    int jobs = 0;
};

void DocAwaiter::await_suspend(std::coroutine_handle<> h) noexcept {
    (void)h;
}
Msg DocAwaiter::await_resume() const noexcept {
    return s->doc;
}

static Task finalize(const KeyMaterial& km, Session& s) {
    Msg doc = co_await DocAwaiter{&s};
    (void)doc;

    u128 p = load_u128(km.p);
    u128 q = load_u128(km.q);
    u128 e = load_u128(km.e);

    u128 n = p * q;
    out("modulus " + u128_hex(n) + "\n");

    if (p <= 1 || q <= 1) { out("finalize aborted\n"); co_return; }

    u128 lam = lcm_u(p - 1, q - 1);
    if (lam == 0 || gcd_u(e % lam, lam) != 1) {
        out("finalize aborted\n");
        co_return;
    }
    u128 d = mod_inv(e, lam);
    store_u128(const_cast<KeyMaterial&>(km).p, d);
    out("finalized\n");
    co_return;
}

static void do_prepare(Session& s) {
    if (s.jobs >= 16) { out("job limit reached\n"); return; }
    s.jobs++;

    out("e> "); std::string es = read_line();
    out("p> "); std::string ps = read_line();
    out("q> "); std::string qs = read_line();

    if (s.armed && s.frame) {
        if (s.frame.done()) s.frame.destroy();
        s.armed = false;
    }

    void* cell = g_slab.alloc();
    if (!cell) { out("no capacity\n"); return; }
    KeyMaterial* km = new (cell) KeyMaterial();
    memset(km, 0, sizeof(*km));
    set_bigint(km->e, from_hex(es));
    set_bigint(km->p, from_hex(ps));
    set_bigint(km->q, from_hex(qs));
    km->tag = 0x4e4f54415259ULL;

    Task t = finalize(*km, s);
    s.frame = t.h;
    s.armed = true;

    g_slab.release(km);
    out("job staged\n");
}

static void do_submit(Session& s) {
    if (!s.armed || !s.frame || s.frame.done()) { out("no staged job\n"); return; }
    out("doc> "); std::string ds = read_line();
    s.doc.data = from_hex(ds);
    s.frame.resume();
}

static void do_addcipher(Session& s) {
    out("kind (1 notary / 2 b64 / 3 rot)> ");
    std::string k = read_line();
    if (k == "1") {
        void* cell = g_slab.alloc();
        if (!cell) { out("no capacity\n"); return; }
        s.signer = new (cell) Notary();
        out("notary ready\n");
    } else if (k == "2") {
        struct B64 : Signer {
            std::string buf;
            void run(Msg& m) override { out("b64 " + to_hex(m.data) + "\n"); }
        };
        s.signer = new B64();
        out("codec ready\n");
    } else if (k == "3") {
        struct Rot : Signer {
            std::string buf;
            void run(Msg& m) override {
                std::vector<uint8_t> r = m.data;
                for (auto& b : r) b = (uint8_t)(b + 13);
                out("rot " + to_hex(r) + "\n");
            }
        };
        s.signer = new Rot();
        out("codec ready\n");
    } else {
        out("unknown kind\n");
    }
}

static void do_sign(Session& s) {
    if (!s.signer) { out("no signer\n"); return; }
    out("msg> "); std::string ms = read_line();
    Msg m; m.data = from_hex(ms);
    s.signer->run(m);
}

int main() {
    setvbuf(stdin, nullptr, _IONBF, 0);
    setvbuf(stdout, nullptr, _IONBF, 0);

    Session s;
    out("attest streaming notary\n");
    while (true) {
        out("[1 prepare / 2 submit / 3 cipher / 4 sign / 5 quit]> ");
        std::string line = read_line();
        if (line.empty() && feof(stdin)) break;
        if (line == "1") do_prepare(s);
        else if (line == "2") do_submit(s);
        else if (line == "3") do_addcipher(s);
        else if (line == "4") do_sign(s);
        else if (line == "5") { out("bye\n"); break; }
        else out("?\n");
    }
    return 0;
}
