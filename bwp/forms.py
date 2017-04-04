# -*- coding: utf-8 -*-
#
#  bwp/forms.py
#
#  Copyright 2013 Grigoriy Kramarenko <root@rosix.ru>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
from __future__ import unicode_literals

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy, ugettext as _

from bwp.models import TempUploadFile

ERROR_MESSAGE = ugettext_lazy(
    "Please enter the correct username and password "
    "for a staff account. Note that both fields are case-sensitive.")


class BWPAuthenticationForm(AuthenticationForm):
    """
    A custom authentication form used in the bwp app.

    """
    this_is_the_login_form = forms.BooleanField(
        widget=forms.HiddenInput,
        initial=1,
        error_messages={
            'required': ugettext_lazy(
                "Please log in again, because your session has expired."
            )
        }
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        message = ERROR_MESSAGE

        if username and password:
            self.user_cache = authenticate(username=username,
                                           password=password)
            if self.user_cache is None:
                if '@' in username:
                    # Mistakenly entered e-mail address instead of username?
                    # Look it up.
                    try:
                        user = User.objects.get(email=username)
                    except (User.DoesNotExist, User.MultipleObjectsReturned):
                        # Nothing to do here, moving along.
                        pass
                    else:
                        if user.check_password(password):
                            message = _(
                                "Your e-mail address is not your username."
                                " Try '%s' instead.") % user.username
                raise forms.ValidationError(message)
            elif not self.user_cache.is_active or not self.user_cache.is_staff:
                raise forms.ValidationError(message)

        return self.cleaned_data


class TempUploadFileForm(forms.ModelForm):
    class Meta:
        model = TempUploadFile
        fields = ('file',)
