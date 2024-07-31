from utils import req


def run_tests_users():
    res = req("user/me")
    print(res)


def test_user_me():
    res = req("user/me")
