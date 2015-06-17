import json
import mock
import urlparse


def assert_object(obj, **kwargs):
    """Validates object."""
    for k, v in kwargs.items():
        value = getattr(obj, k)
        try:
            assert v == value
        except AssertionError:
            raise ValueError('Value {} does not match {}'.format(v, value))


def verify_email(messages, num, mail_to, in_list):
    """Verifies email message.

    Args:
        message: EmailMessage object
        num: Number of messages
        to: Mail recipient list or string for each message
        in_list: Substring list in each message
    """
    assert num == len(messages)
    if num == 1:
        mail_to, in_list = [mail_to], [in_list]
    for i in range(num):
        message = messages[i]
        # message.body is instance of mail.EncodedPayload
        mail_content = message.body.decode()
        assert mail_to[i] == message.to
        for in_str in in_list[i]:
            assert in_str in mail_content


def verify_invalid_methods(client, invalid_methods, endpoint):
    """Verifies invalid methods."""
    ec_invalid_method = dict(
        message='Method not allowed', code='invalid_method')
    for method in invalid_methods:
        resp = getattr(client, method)(endpoint)
        data = json.loads(resp.data)
        assert ec_invalid_method == data
        assert 405 == resp.status_code


def execute_queue_task(client, task):
    """Executes push queue task."""
    data = urlparse.parse_qs(task.payload)
    return getattr(client, task.method.lower())(
        task.url, data=data)


def verify_push_notifications(taskq, client, data):
    """Verifies push notification tasks."""
    tasks = taskq.get_filtered_tasks(queue_names='push')
    assert 2 == len(tasks)
    # Android task
    with mock.patch('eucaby_api.tasks.gcm.GCM.json_request') as req_mock:
        req_mock.return_value = {}
        resp_android = execute_queue_task(client, tasks[0])

        # Test GCM request
        assert 1 == req_mock.call_count
        req_mock.assert_called_with(
            registration_ids=['12'], data=data, retries=7)
        assert 200 == resp_android.status_code

    # iOS task
    with mock.patch(
        'eucaby_api.tasks.api_utils.create_apns_socket'
    ) as mock_create_socket:
        apns_socket = mock.Mock()
        mock_create_socket.return_value = apns_socket
        # Test APNs request
        mock_send_notif = apns_socket.gateway_server.send_notification_multiple
        resp_ios = execute_queue_task(client, tasks[1])
        assert 1 == mock_send_notif.call_count
        assert 200 == resp_ios.status_code
