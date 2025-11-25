"""
Step definitions voor berichten (AWB Art. 3:40-3:45)

Wettelijke grondslag:
- AWB Art. 3:40: Bekendmaking van besluiten
- AWB Art. 3:41: Toezending/uitreiking
- AWB Art. 3:45: Rechtsmiddelenclausule
- AWIR Art. 13: Elektronisch berichtenverkeer
"""

from unittest import TestCase

from behave import then, when

from machine.events.message.aggregate import MessageStatus, MessageType

assertions = TestCase()


# === Bericht aanmaak en verificatie ===


@then('is er een bericht aangemaakt voor BSN "{bsn}"')
@when('is er een bericht aangemaakt voor BSN "{bsn}"')
def step_impl(context, bsn):
    """Controleer of er een bericht is aangemaakt voor de burger"""
    messages = context.services.message_manager.get_messages_by_bsn(bsn, include_archived=True)
    assertions.assertGreater(
        len(messages),
        0,
        f"Expected at least one message for BSN {bsn}, but found none",
    )
    # Store the latest message in context for further assertions
    context.last_message = messages[0] if messages else None


@then('is het bericht type "{message_type}"')
def step_impl(context, message_type):
    """Controleer het type van het bericht"""
    assertions.assertIsNotNone(context.last_message, "No message found in context")
    expected_type = MessageType(message_type)
    actual_type = context.last_message.message_type
    # Handle both enum and string types
    actual_value = actual_type.value if hasattr(actual_type, "value") else actual_type
    assertions.assertEqual(
        actual_value,
        expected_type.value,
        f"Expected message type {message_type}, but was {actual_value}",
    )


@then('bevat het bericht onderwerp "{expected_text}"')
def step_impl(context, expected_text):
    """Controleer of het onderwerp de verwachte tekst bevat (case-insensitive)"""
    assertions.assertIsNotNone(context.last_message, "No message found in context")
    assertions.assertIn(
        expected_text.lower(),
        context.last_message.onderwerp.lower(),
        f"Expected '{expected_text}' in onderwerp, but onderwerp was '{context.last_message.onderwerp}'",
    )


@then("bevat het bericht de rechtsmiddelenclausule")
def step_impl(context):
    """Controleer of het bericht de rechtsmiddelenclausule bevat (AWB Art. 3:45)"""
    assertions.assertIsNotNone(context.last_message, "No message found in context")
    assertions.assertIsNotNone(
        context.last_message.rechtsmiddel_info,
        "Expected rechtsmiddel_info to be present, but it was None",
    )
    # De rechtsmiddelenclausule moet informatie bevatten over bezwaar
    assertions.assertIn(
        "bezwaar",
        context.last_message.rechtsmiddel_info.lower(),
        "Expected rechtsmiddel_info to contain information about bezwaar",
    )


# === Bericht status ===


@then('is het bericht status "{status}"')
def step_impl(context, status):
    """Controleer de status van het bericht"""
    assertions.assertIsNotNone(context.last_message, "No message found in context")
    expected_status = MessageStatus(status)
    actual_status = context.last_message.status
    # Handle both enum and string types
    actual_value = actual_status.value if hasattr(actual_status, "value") else actual_status
    assertions.assertEqual(
        actual_value,
        expected_status.value,
        f"Expected message status {status}, but was {actual_value}",
    )


@then("is het bericht ongelezen")
def step_impl(context):
    """Controleer of het bericht ongelezen is"""
    assertions.assertIsNotNone(context.last_message, "No message found in context")
    assertions.assertTrue(
        context.last_message.is_unread,
        f"Expected message to be unread, but status was {context.last_message.status.value}",
    )


@then("is het bericht gelezen")
def step_impl(context):
    """Controleer of het bericht gelezen is"""
    assertions.assertIsNotNone(context.last_message, "No message found in context")
    assertions.assertFalse(
        context.last_message.is_unread,
        f"Expected message to be read, but status was {context.last_message.status.value}",
    )


# === Bericht acties ===


@when("de burger het bericht leest")
def step_impl(context):
    """Markeer het bericht als gelezen"""
    assertions.assertIsNotNone(context.last_message, "No message found in context")
    message_id = str(context.last_message.id)
    context.services.message_manager.mark_as_read(message_id)
    # Refresh the message from the repository
    context.last_message = context.services.message_manager.get_message_by_id(message_id)


@when("de burger het bericht archiveert")
def step_impl(context):
    """Archiveer het bericht"""
    assertions.assertIsNotNone(context.last_message, "No message found in context")
    message_id = str(context.last_message.id)
    context.services.message_manager.archive_message(message_id)
    # Refresh the message from the repository
    context.last_message = context.services.message_manager.get_message_by_id(message_id)


# === Ongelezen telling ===


@then('is het aantal ongelezen berichten {count:d} voor BSN "{bsn}"')
def step_impl(context, count, bsn):
    """Controleer het aantal ongelezen berichten"""
    actual_count = context.services.message_manager.get_unread_count(bsn)
    assertions.assertEqual(
        actual_count,
        count,
        f"Expected {count} unread messages for BSN {bsn}, but found {actual_count}",
    )


# === Berichten per zaak ===


@then("is er een bericht gekoppeld aan de zaak")
def step_impl(context):
    """Controleer of er een bericht is gekoppeld aan de huidige zaak"""
    assertions.assertIsNotNone(context.case_uuid, "No case found in context")
    messages = context.services.message_manager.get_messages_by_case(str(context.case_uuid))
    assertions.assertGreater(
        len(messages),
        0,
        f"Expected at least one message for case {context.case_uuid}, but found none",
    )
    # Store for further assertions
    context.case_messages = messages


@then("zijn er {count:d} berichten voor de zaak")
def step_impl(context, count):
    """Controleer het aantal berichten voor de zaak"""
    assertions.assertIsNotNone(context.case_uuid, "No case found in context")
    messages = context.services.message_manager.get_messages_by_case(str(context.case_uuid))
    assertions.assertEqual(
        len(messages),
        count,
        f"Expected {count} messages for case {context.case_uuid}, but found {len(messages)}",
    )
