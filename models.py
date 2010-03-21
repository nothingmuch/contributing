#!/usr/bin/env python
#
# Copyright 2010 Brad Fitzpatrick
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from google.appengine.api import users
from google.appengine.ext import db

import logging
import sha

SALT = 'Contributing!'

class User(db.Model):
  """A user's global state, not specific to a project."""
  # One of these will be set:
  google_user = db.UserProperty(indexed=True, required=False)
  openid_user = db.StringProperty(indexed=True, required=False)

  url = db.StringProperty(indexed=False)
  last_login = db.DateTimeProperty(auto_now=True)

  @property
  def last_login_short(self):
    return str(self.last_login)[0:10]

  @property
  def display_name(self):
    if self.google_user:
      return self.google_user.email
    if self.openid_user:
      return self.openid_user
    return "Unknown user type"

  @property
  def public_name(self):
    if self.google_user:
      email = self.google_user.email()
      return email[0:email.find('@')+1] + "..."
    if self.openid_user:
      return self.openid_user
    return "Unknown user type"

  @property
  def profile_page_url(self):
    return "/u/" + self.sha1_key

  @property
  def sha1_key(self):
    if self.google_user:
      return sha.sha(self.google_user.email() + SALT).hexdigest()[0:8]
    if self.openid_user:
      return sha.sha(self.openid_user + SALT).hexdigest()[0:8]
    return Exception("unknown user type")

  def LogOut(self, handler, next_url):
    if self.google_user:
      handler.redirect(users.create_logout_url(next_url))
      return
    handler.response.headers.add_header(
      'Set-Cookie', 'session=; path=/')
    handler.redirect(next_url)

  def GetOrCreateFromDatastore(self):
    return User.get_or_insert(self.sha1_key,
                              google_user=self.google_user,
                              openid_user=self.openid_user)


class Project(db.Model):
  """A project which can be contributed to, with its metadata."""
  pretty_name = db.StringProperty(required=False)
  owner = db.ReferenceProperty(User, required=True)
  last_edit = db.DateTimeProperty(auto_now=True)

  how_to = db.TextProperty(default="")
  code_repo = db.StringProperty(indexed=False, default="")
  home_page = db.StringProperty(indexed=False, default="")
  bug_tracker = db.StringProperty(indexed=False, default="")
  irc_channel = db.StringProperty(indexed=False, default="")
  mailing_list = db.StringProperty(indexed=False, default="")

  @property
  def name(self):
    return self.key().name()

  @property
  def display_name(self):
    if self.pretty_name:
      return self.pretty_name
    return self.name

  @property
  def last_edit_short(self):
    return str(self.last_edit)[0:10]


class Contributor(db.Model):
  """A user-project tuple."""
  user = db.ReferenceProperty(User, required=True)
  project = db.ReferenceProperty(Project, required=True)

  is_active = db.BooleanProperty()
  role = db.StringProperty()  # e.g. "Founder" freeform.
  
  
