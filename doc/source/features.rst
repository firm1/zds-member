========
Features
========

Sign up
========

The registration of a member is in two phases:

- The member creates their account and provides a username, a password and valid email address.
- A confirmation email is sent with a token that will activate the account.

.. Warning::

     - Commas are not allowed in the nickname, which also can not begin or end with spaces.
     - The password must be at least 6 characters.

Unsuscribe
==========

Promote member
==============

In order to manage the members directly from the site (ie without having to go through the Django admin interface), a promote interface was developed. This interface allows:

1. Add / Remove a member / group (s)
2. Add / Delete superuser status to a member
3. (De) activate an account

First point allows to pass a member in new group. If other groups are emerging (validator) then it will be possible here also to change it. The second point can provide access to the member at the django interface and this promotion interface. Finally, the last point simply concerns the account activation (normally made by the Member at registration).

It is managed by the PromoteMemberForm form available in the ``zds/member/forms.py``. It's then visible through the template ``member/settings/promote.html`` that may be accessed as root user by the profile of any member.


Add karma
=========


Reset Password
==============

When a member forgets their password, you can reset it. The old password is deleted and the user can choose a new one. For this, he went on the password reset page (``members/reinitialisation /) from the login page.

On this page the user has to enter his username or email address. For this, click on the link to the form. When the user clicks the submit button, a token is randomly generated and is stored in a database.

A message is sent to the user's email address. This email contains a reset link. This link contains a parameter, the reset token and directs the user to address ``members/new_password/``.

This page allows you to change the user's password. The user completes the form and clicks the submit button. If the password and the confirmation field and the corresponding password is business rules, the password is changed. The system displays a message confirming the password change.

.. Warning::

    - The password must be at least 6 characters.
    - The link is valid for one hour. If the user does not click on the link in the allotted time, an error message is displayed.
    - The password reset token is valid only once. If the user tries to change their password with the same token, a 404 page is displayed to the user.