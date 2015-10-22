========
REST API
========

.. http:get:: /api/(int:user_id)/

   Gets a user given by its identifier.

   **Example request**:

   .. sourcecode:: http

      GET /api/800/ HTTP/1.1
      Host: example.com
      Accept: application/json, text/javascript

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Vary: Accept
      Content-Type: text/javascript
      {
         "pk": 800,
         "username": "firm1",
         "is_active": true,
         "date_joined": "2014-07-28T02:57:31",
         "site": "http://zestedesavoir.com",
         "avatar_url": "http://static.wamiz.fr/images/animaux/rongeurs/large/souris.jpg",
         "biography": "I'm beautiful",
         "sign": "cool",
         "show_email": false,
         "show_sign": true,
         "hover_or_click": true,
         "email_for_answer": false,
         "last_visit": "2015-10-20T03:24:06"
      }

   :param user_id: user's unique id
   :type user_id: int
   :statuscode 200: no error
   :statuscode 404: there's no user with this id

.. http:get:: /api/mon-profil/

   Gets informations about identified member

   :statuscode 200: no error
   :statuscode 401: user are not authenticated
   :reqheader Authorization: OAuth2 token to authenticate

.. http:get:: /api/

   List of website's members

   :query page_size: number of users. default is 10
   :statuscode 200: no error

.. http:put:: /api/(int:user_id)/

   Updates a user given by its identifier.

   :param user_id: user's unique id
   :type user_id: int
   :jsonparam int pk: user's unique id
   :statuscode 200: no error
   :statuscode 404: there's no user with this id
   :reqheader Authorization: OAuth2 token to authenticate

.. http:post:: /api/(int:user_id)/lecture-seule/

   Applies a read only sanction at a user given.

   :param user_id: user's unique id
   :type user_id: int
   :jsonparam int pk: user id to read only
   :jsonparam string ls-jrs: Number of days for the sanction.
   :jsonparam string ls-text: Description of the sanction.
   :statuscode 200: no error
   :statuscode 401: Not authenticated
   :statuscode 403: Insufficient rights to call this procedure. Must to be a staff user.
   :statuscode 401: Not found
   :reqheader Authorization: OAuth2 token to authenticate

.. http:post:: /api/(int:user_id)/ban/

   Applies a ban sanction at a user given.

   :param user_id: user's unique id
   :type user_id: int
   :jsonparam int pk: user id to ban
   :jsonparam string ban-jrs: Number of days for the sanction.
   :jsonparam string ban-text: Description of the sanction.
   :statuscode 200: no error
   :statuscode 401: Not authenticated
   :statuscode 403: Insufficient rights to call this procedure. Must to be a staff user.
   :statuscode 401: Not found
   :reqheader Authorization: OAuth2 token to authenticate

.. http:delete:: /api/(int:user_id)/lecture-seule

   Removes a read only sanction at a user given.

   :param user_id: user's unique id
   :type user_id: int
   :jsonparam int pk: id of read only user
   :statuscode 200: no error
   :statuscode 401: Not authenticated
   :statuscode 403: Insufficient rights to call this procedure. Must to be a staff user.
   :statuscode 401: Not found
   :reqheader Authorization: OAuth2 token to authenticate

.. http:delete:: /api/(int:user_id)/ban/

   Removes a ban sanction at a user given.

   :param user_id: user's unique id
   :type user_id: int
   :jsonparam int pk: id of banned user
   :statuscode 200: no error
   :statuscode 401: Not authenticated
   :statuscode 403: Insufficient rights to call this procedure. Must to be a staff user.
   :statuscode 401: Not found
   :reqheader Authorization: OAuth2 token to authenticate
