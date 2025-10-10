from machine.nrml.value_providers.source_reference import SelectOnField, SourceReference


class TestSelectOnField:
    """Test cases for SelectOnField dataclass"""

    def test_create_select_on_field(self):
        """Test creating a SelectOnField instance"""
        field = SelectOnField(name="bsn", description="Burgerservicenummer", type="string", value="$BSN")

        assert field.name == "bsn"
        assert field.description == "Burgerservicenummer"
        assert field.type == "string"
        assert field.value == "$BSN"


class TestSourceReference:
    """Test cases for SourceReference"""

    def test_from_dict_with_select_on(self):
        """Test creating SourceReference from dict with select_on fields"""
        data = {
            "table": "personen",
            "field": "nationaliteit",
            "select_on": [
                {"name": "bsn", "description": "Burgerservicenummer van de persoon", "type": "string", "value": "bsn"}
            ],
        }

        source_ref = SourceReference.from_dict(data)

        assert source_ref.table == "personen"
        assert source_ref.field == "nationaliteit"
        assert len(source_ref.select_on) == 1
        assert source_ref.select_on[0].name == "bsn"
        assert source_ref.select_on[0].description == "Burgerservicenummer van de persoon"
        assert source_ref.select_on[0].type == "string"
        assert source_ref.select_on[0].value == "bsn"

    def test_from_dict_with_multiple_select_on(self):
        """Test creating SourceReference with multiple select_on fields"""
        data = {
            "table": "addresses",
            "field": "postal_code",
            "select_on": [
                {"name": "city", "description": "City name", "type": "string", "value": "$CITY"},
                {"name": "street", "description": "Street name", "type": "string", "value": "$STREET"},
            ],
        }

        source_ref = SourceReference.from_dict(data)

        assert source_ref.table == "addresses"
        assert source_ref.field == "postal_code"
        assert len(source_ref.select_on) == 2
        assert source_ref.select_on[0].name == "city"
        assert source_ref.select_on[0].value == "$CITY"
        assert source_ref.select_on[1].name == "street"
        assert source_ref.select_on[1].value == "$STREET"

    def test_from_dict_with_empty_select_on(self):
        """Test creating SourceReference with empty select_on list"""
        data = {"table": "products", "field": "price", "select_on": []}

        source_ref = SourceReference.from_dict(data)

        assert source_ref.table == "products"
        assert source_ref.field == "price"
        assert source_ref.select_on == []

    def test_from_dict_without_select_on(self):
        """Test creating SourceReference without select_on field"""
        data = {"table": "settings", "field": "max_value"}

        source_ref = SourceReference.from_dict(data)

        assert source_ref.table == "settings"
        assert source_ref.field == "max_value"
        assert source_ref.select_on == []

    def test_direct_construction(self):
        """Test creating SourceReference directly"""
        select_on_fields = [SelectOnField(name="id", description="Identifier", type="number", value="$ID")]

        source_ref = SourceReference(table="users", field="email", select_on=select_on_fields)

        assert source_ref.table == "users"
        assert source_ref.field == "email"
        assert len(source_ref.select_on) == 1
        assert source_ref.select_on[0].name == "id"

    def test_from_dict_preserves_all_select_on_fields(self):
        """Test that all select_on field properties are preserved"""
        data = {
            "table": "employees",
            "field": "salary",
            "select_on": [
                {
                    "name": "employee_id",
                    "description": "Unique employee identifier",
                    "type": "integer",
                    "value": "$EMP_ID",
                }
            ],
        }

        source_ref = SourceReference.from_dict(data)

        select_on = source_ref.select_on[0]
        assert select_on.name == "employee_id"
        assert select_on.description == "Unique employee identifier"
        assert select_on.type == "integer"
        assert select_on.value == "$EMP_ID"
