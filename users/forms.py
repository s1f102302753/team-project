from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import CustomUser, Municipality

class CustomLoginForm(AuthenticationForm):
    municipality_id = forms.CharField(label="自治体ID", max_length=100)

class CustomUserCreationForm(UserCreationForm):
    user_type = forms.ChoiceField(
        choices=[('resident', '住民'), ('official', '自治体職員')],
        label='アカウント種別',
        widget=forms.RadioSelect
    )
    municipality = forms.ModelChoiceField(
        queryset=Municipality.objects.all(),
        required=False,
        label='所属自治体（職員のみ）'
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'user_type', 'municipality', 'password1', 'password2')
        labels = {
            'username': 'ユーザー名',
            'email': 'メールアドレス',
            'password1': 'パスワード',
            'password2': 'パスワード（確認）',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 各フィールドのhelp_textを削除
        for field in self.fields.values():
            field.help_text = ''

    def save(self, commit=True):
        user = super().save(commit=False)
        user_type = self.cleaned_data['user_type']
        if user_type == 'official':
            user.is_official = True
            user.is_resident = False
            user.municipality = self.cleaned_data['municipality']
        else:
            user.is_official = False
            user.is_resident = True
            user.municipality = None

        if commit:
            user.save()
        return user