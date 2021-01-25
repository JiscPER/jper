class AccountException(Exception):
    pass

class EmailInUseException(AccountException):
    pass

class IncorrectPasswordException(AccountException):
    pass

class NonUniqueAccountException(AccountException):
    pass

class AccountNotFoundException(AccountException):
    pass

class EmailFailedException(AccountException):
    pass

class CannotLoginException(AccountException):
    pass