from app.domain.sharedkernel.model.Id import Id


class ObjectKeyPolicy:
    """Build the deterministic storage key (pointer) for an object/version blob.

    Pure, no IO. Naming a blob's location is a business convention, not a storage
    backend concern, so it lives here rather than inside the StorageService
    implementation. The key is deterministic: the same input always yields the
    same key, so a retried upload overwrites in place instead of creating a
    duplicate object in storage.

    Xây key lưu trữ (pointer) cố định cho blob của object/version. Thuần, không IO.
    Đặt tên vị trí blob là quy ước nghiệp vụ, không phải việc của storage backend
    nên đặt ở đây thay vì trong implementation của StorageService. Key cố định:
    cùng input luôn ra cùng key nên upload lặp lại ghi đè đúng chỗ, không nhân bản.
    """

    def build(self, owner_id: Id, entity_id: Id, filename: str) -> str:
        # owner prefix (4 bytes) / full entity hex / sanitized filename.
        # `entity_id` is the object id for the first upload and the version id for
        # subsequent versions, keeping every blob at a unique, stable location.
        # tiền tố owner (4 byte) / hex entity đầy đủ / tên file đã làm sạch.
        # `entity_id` là object id cho lần upload đầu và version id cho version sau,
        # giữ mỗi blob ở một vị trí duy nhất, ổn định.
        owner_prefix = owner_id.to_bytes().hex()[:8]
        entity_hex = entity_id.to_bytes().hex()

        # Strip every directory component so a crafted filename like
        # "../../other_owner/obj/x" cannot escape the {owner}/{entity} prefix.
        # The StorageService backend also rejects traversal keys, but sanitizing
        # here keeps the stored layout predictable.
        # Cắt mọi thành phần thư mục để tên file độc hại không thoát prefix
        # {owner}/{entity}. Backend StorageService cũng từ chối key traversal,
        # nhưng làm sạch ở đây giữ layout lưu trữ dễ đoán.
        safe_name = filename.replace("\\", "/").split("/")[-1]
        if not safe_name or safe_name in (".", ".."):
            safe_name = "upload"

        return f"{owner_prefix}/{entity_hex}/{safe_name}"
