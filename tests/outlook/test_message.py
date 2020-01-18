# import pytest


class TestMessage:
    def test___str__(self):  # synced
        assert True

    def test___hash__(self):  # synced
        assert True

    def test__repr_html_(self):  # synced
        assert True

    def test_text(self):  # synced
        assert True

    def test_markup(self):  # synced
        assert True

    def test_fluent(self):  # synced
        assert True

    def test_reply(self):  # synced
        assert True

    def test_forward(self):  # synced
        assert True

    def test_copy(self):  # synced
        assert True

    def test_render(self):  # synced
        assert True

    def test_save_attachments_to(self):  # synced
        assert True

    class TestAttributes:
        class TestFrom:
            pass

        class TestSender:
            pass

        class TestSubject:
            pass

        class TestReceivedOn:
            pass

        class TestLastModified:
            pass

        class TestCategories:
            pass

        class TestIsRead:
            pass

        class TestHasAttachments:
            pass

        class TestIsDraft:
            pass

        class TestHasDeliveryReceipt:
            pass

        class TestHasReadReceipt:
            pass

        class TestImportance:
            pass

        class TestBody:
            pass

        class TestCc:
            pass

        class TestBcc:
            pass

        class TestTo:
            pass


class TestBulkMessageAction:
    def test_copy(self):  # synced
        assert True

    def test_move(self):  # synced
        assert True

    def test_delete(self):  # synced
        assert True

    def test_mark_as_read(self):  # synced
        assert True

    def test_save_draft(self):  # synced
        assert True


class TestMessageQuery:
    def test_bulk(self):  # synced
        assert True

    def test_execute(self):  # synced
        assert True


class TestFluentMessage:
    def test_from_(self):  # synced
        assert True

    def test_to(self):  # synced
        assert True

    def test_cc(self):  # synced
        assert True

    def test_bcc(self):  # synced
        assert True

    def test_request_read_receipt(self):  # synced
        assert True

    def test_request_delivery_receipt(self):  # synced
        assert True

    def test_send(self):  # synced
        assert True
