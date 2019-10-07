from __future__ import annotations

import miscutils
import office


class Config(miscutils.Config):
    app_name = office.__name__
    default = {"default_account": "", "accounts": {}}

    def add_account(self, account: str, password: str = None, is_default: bool = False) -> None:
        self.data.accounts[account] = miscutils.NameSpaceDict(account=account, password=password)
        if is_default:
            self.set_default(account=account)

    def set_default(self, account: str):
        self.data.default_account = account
