# Hướng dẫn migrate data-service sang gRPC client SDK + mTLS động

> Viết 2026-06-13 cho phiên sau làm trực tiếp tại repo data-service. Gói trọn cả
> phần dọn dẹp SSL provider (trước nằm ở `don-dep-ssl-provider.md`) lẫn phần
> migrate client. Đọc kèm tài liệu framework:
> `xime framework/.claude/docs/grpc-client-mtls-plan.md` và
> `D:/tài liệu/xime/grpc-code-first-server-client-mtls.md`.

## 0. Bối cảnh - cái gì đã xong, cái gì còn lại

Framework Xime đã hỗ trợ trọn bộ (Phase 0-4): server mTLS động qua
`configure_grpc_tls(provider=...)`, client SDK sinh từ `.proto`
(`xime grpc client`), DI qua `configure_grpc_clients` + YAML `grpc.clients.<id>`,
và channel mTLS động (`tls.dynamic: true` - tự rebuild khi cert rotate).

**data-service đã làm phần wiring server:**

- `app/integration/trust/ssl/TrustGrpcCertificateProvider.py` đã có (implement
  `GrpcCertificateProvider` của framework, đọc 2 resolver).
- `config/grpc.py` đã gọi `configure_grpc_tls(provider=TrustGrpcCertificateProvider)`.
- `resources/application.yml` đã bật `grpc.tls.enabled: true, mutual: true`.

**Còn lại (việc của phiên này):** dọn dẹp code thừa phía server + migrate client
gọi Trust sang SDK. Làm theo Phần A rồi Phần B.

> Chạy `pytest` trước và sau mỗi phần để biết mình không làm hỏng gì.

---

## Phần A - Dọn dẹp server mTLS (xóa code thừa)

Server gRPC inbound giờ lấy cert động từ provider ở mỗi handshake. Mọi cơ chế
"đẩy" credentials thủ công đã thừa.

### A1. Xóa `app/integration/trust/ssl/GrpcServerSslContextProvider.py`

Class này build `grpc.ServerCredentials` thủ công nhưng chưa bao giờ có chỗ cắm
vào `GrpcAdapter` (server từng chạy insecure). Framework giờ tự build credentials
từ provider → class này hoàn toàn thừa. Xóa file.

### A2. Sửa `app/integration/trust/startup/TrustStartupOrchestrator.py`

Bỏ dependency `server_ssl: GrpcServerSslContextProvider` khỏi `__init__` và bỏ
bước `self._server_ssl.reload()` (bước 3 trong `post_construct`). Thứ tự còn lại
giữ nguyên và VẪN QUAN TRỌNG:

1. Load root CA (`root_ca_init.initialize()`)
2. Sync mTLS cert (`cert_sync.synchronize_on_startup()`) - nạp cert vào resolver
3. ~~Build server SSL~~ - XÓA
4. Sync verification keys (`key_sync.synchronize()`)

Cập nhật docstring cho khớp. Lý do giữ thứ tự: provider đọc resolver lười ở
handshake/call đầu, nên resolver phải được nạp cert (bước 2) trước khi adapter
phục vụ request đầu tiên.

### A3. Sửa `app/integration/trust/scheduler/CertRotationJob.py`

Sau khi migrate client (Phần B) xong, job này rút gọn còn:

```python
async def run(self) -> None:
    await self._cert_sync.synchronize()
    # Không còn key_client.reset_channel() (XimeGrpcChannel tự rebuild)
    # Không còn server_ssl.reload() (server credentials động tự nhặt cert)
```

Bỏ luôn dependency `server_ssl` và `key_client` khỏi `__init__`. (Nếu làm Phần A
trước Phần B thì tạm bỏ `server_ssl`, để `key_client.reset_channel()` lại, xóa
nốt khi Phần B xong.)

### A4. Dọn DI

Trong `config/dependency.py`, `GrpcServerSslContextProvider` được tạo qua
auto-scan package `app.integration.trust.ssl`. Sau khi xóa file, kiểm tra không
còn import/bind nào trỏ tới nó. `TrustSslContextProvider` (client credentials)
thì GIỮ LẠI - xem ranh giới ở Phần B.

### A5. Chạy app + pytest

App phải start được, server gRPC nghe cổng 50051 với mTLS (không còn insecure).

---

## Phần B - Migrate client gọi Trust sang SDK

### Ranh giới quan trọng (đọc trước khi làm)

data-service có HAI client outbound tới Trust, vai trò khác nhau:

| Client | Vai trò | Migrate? |
|---|---|---|
| `TrustKeyClient` (`key/`) | Consumer thường: lấy public key để verify JWT, dùng cert runtime | ✅ CÓ - sang SDK + XimeGrpcChannel động |
| `GrpcTrustCertificateClient` (`certificate/`) | Bootstrap: đổi refresh token lấy cert, dùng cert bootstrap rồi cert runtime | ⛔ KHÔNG - giữ viết tay |

**Vì sao giữ `GrpcTrustCertificateClient` viết tay:** nó chính là đường *lấy
cert*. Call đầu tiên (`synchronize_on_startup`) xảy ra khi resolver còn RỖNG, dùng
cert bootstrap từ file. Nếu chuyển nó sang `tls.dynamic` (đọc cert runtime từ
resolver) sẽ tạo vòng lặp chết: cần cert runtime để gọi Trust, nhưng cert runtime
lại do chính call này lấy về. Đây là hạ tầng bootstrap đặc thù, không phải RPC
nghiệp vụ thông thường - framework client SDK không dành cho nó. Giữ nguyên
`GrpcTrustCertificateClient` + `TrustSslContextProvider`.

### B1. Sinh SDK từ proto của Trust

Proto sẵn có ở `app/integration/trust/proto/dependency/trust/key/key_distribution.proto`
(định nghĩa `KeyDistributionService.GetPublicKeys`). Copy proto cần thiết vào một
thư mục contracts (Trust là service Java, KHÔNG có sidecar `contract.json` →
generator chạy chế độ proto-only, chỉ sinh method unary, đủ cho key API):

```bash
mkdir -p contracts/trust
cp app/integration/trust/proto/dependency/trust/key/key_distribution.proto contracts/trust/
# copy kèm mọi proto mà nó import (nếu có)
xime grpc client --proto contracts/trust --out clients/trust
```

Kết quả `clients/trust/` chứa client class (ví dụ `KeyDistributionServiceClient`)
+ Pydantic model (`GetPublicKeysRequest`, `GetPublicKeysResponse`...). Commit
`contracts/trust/` và `clients/trust/` vào git.

> Lưu ý naming: generator strip hậu tố `Controller` (không có ở đây) và đổi rpc
> `GetPublicKeys` → method `get_public_keys`. Kiểm tra tên thật trong
> `clients/trust/_clients.py` sau khi sinh.

### B2. Khai báo client vào DI + YAML

`config/grpc.py`:

```python
from xime.adapters.grpc import configure_grpc_clients
from clients.trust import KeyDistributionServiceClient   # tên thật sau khi sinh

configure_grpc_clients("trust", KeyDistributionServiceClient)
```

`resources/application.yml` - thêm block client (dùng chung cert động với server
qua `TrustGrpcCertificateProvider` đã đăng ký):

```yaml
grpc:
  clients:
    trust:
      host: localhost          # = trust.grpc.host hiện tại
      port: 50052              # = trust.grpc.port hiện tại
      deadline_ms: 3000
      tls:
        enabled: true
        dynamic: true          # rebuild channel khi cert rotate
```

### B3. Biến `TrustKeyClient` thành adapter mỏng quanh SDK

`TrustKeyClient` hiện tự dựng channel (`grpc.aio.secure_channel` +
`ssl_provider.current()`) và gọi stub. Thay bằng: nhận `KeyDistributionServiceClient`
(SDK) qua constructor, gọi method của nó, map response sang
`VerificationKeyRecord`. Bỏ `_ensure_stub`, `reset_channel`, `pre_destroy`
(channel do framework quản lý vòng đời). Giữ nguyên `_map_key` (chuyển epoch ms
→ datetime).

```python
class TrustKeyClient:
    def __init__(self, config: RuntimeConfig, keys: KeyDistributionServiceClient):
        self._service_id = config.get("trust.service_id", "data-service")
        self._keys = keys

    async def fetch_public_keys(self) -> list[VerificationKeyRecord]:
        resp = await self._keys.get_public_keys(
            GetPublicKeysRequest(verifier_service_id=self._service_id)
        )
        return [self._map_key(k) for k in resp.keys]
```

Xóa `reset_channel()` ở mọi nơi gọi nó (`CertRotationJob` - xem A3). Cập nhật
`config/dependency.py` nếu cần (bỏ binding `TrustSslContextProvider` cho key
client; provider này vẫn cần cho cert client).

> **Bẫy quan trọng (đã gặp ở data-service 2026-06-13):** SDK dịch lỗi gRPC sang
> exception typed của framework, KHÔNG còn là `grpc.aio.AioRpcError`. Mọi nơi
> đang `except grpc.aio.AioRpcError` quanh lời gọi key client phải đổi sang
> exception typed. Cụ thể `VerificationKeySynchronizer.synchronize()`: đổi nhánh
> bắt `AioRpcError` + check `StatusCode.UNAVAILABLE` thành
> `except RemoteServiceUnavailable` (từ `xime.core.exception.framework`) cho
> nhánh "Trust tắt → fallback DB lặng lẽ (DEBUG)"; bỏ `import grpc`/`grpc.aio`.
> Nếu quên, UNAVAILABLE rơi vào `except Exception` và log WARNING ồn mỗi lần sync
> dù app vẫn chạy đúng.

### B4. Verify outbound

- `KeyRefreshJob` (scheduler) gọi `VerificationKeySynchronizer` → `TrustKeyClient`
  → SDK → Trust. Cert rotate giữa chừng: call kế tiếp tự dùng cert mới (channel
  rebuild theo version). Không cần reset tay.
- Chạy app, kiểm tra log: bootstrap cert (cert client viết tay) → nạp resolver →
  key sync (SDK) chạy được.

---

## Kiểm thử tổng

```bash
pip install -e "D:\code\xime\xime framework"   # đảm bảo framework mới nhất
pip install -e .
pytest                                          # toàn bộ test phải xanh
python app/main.py                              # app start, mTLS cả 2 chiều
```

Tiêu chí xong: server gRPC chạy mTLS động (không insecure); `TrustKeyClient` đi
qua SDK + XimeGrpcChannel; `GrpcServerSslContextProvider` đã xóa;
`CertRotationJob` không còn reset/reload thủ công; `GrpcTrustCertificateClient`
giữ nguyên cho bootstrap.

Khi xong, đây là service mẫu cho notification-service migrate theo
(`notification/.claude/docs/migrate-grpc-client-mtls.md`).
