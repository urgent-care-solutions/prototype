from tortoise import fields, models


class RefreshToken(models.Model):
    id = fields.UUIDField(pk=True)
    user_id = fields.UUIDField(index=True)
    token = fields.CharField(max_length=500, unique=True, index=True)
    expires_at = fields.DatetimeField()
    is_revoked = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "refresh_tokens"
