��    �      �  �   �	      �  f  �  �  P  z   -    �  &  �  �  �  �  �  �     �      C  !     Q"     l"     z"     �"     �"     �"     �"     �"     �"     �"      #     #     "#     0#     >#     N#  "   a#     �#     �#     �#     �#  0   �#  n   �#  	   ^$     h$     m$     q$     �$  ~   �$  
   %     )%     -%     C%     J%     W%     _%     o%     x%     �%     �%     �%     �%     �%  	   �%     �%     �%     �%     �%     &      &     8&     T&     n&     �&  @   �&  W   �&  P   ,'  �   }'  :   (     @(     R(  .   `(     �(  	   �(  >   �(     �(     �(  u   )     �)     �)     �)  �   �)  k   2*  ]   �*  =   �*     :+  (   U+     ~+     �+     �+     �+     �+     �+     �+     �+     �+     �+  
   �+     �+     ,     ',     3,     I,     Q,     V,     d,     l,     r,     �,  
   �,     �,  
   �,     �,     �,     �,     �,     �,     �,  	   �,     �,     -  	   -     -     $-     0-     7-  	   J-     T-     `-     f-     |-     �-     �-     �-     �-     �-     �-     �-     �-     �-     �-     �-     .     .     #.     (.     9.     A.     F.  	   T.     ^.  �  g.    �/  �  5  �   �7  r  �8  �  G:  m	  �;  �  fE    K  �  L  �  �M     �O     �O  "   �O     �O     
P  5   P  %   UP     {P  &   �P  $   �P     �P  $   �P     Q     +Q  -   DQ  '   rQ  8   �Q     �Q     �Q  7   �Q  
   5R  [   @R  �   �R     mS     |S     �S  !   �S  1   �S  �   �S     �T     �T  !   �T  
   U     %U  
   ;U     FU     eU  !   xU     �U     �U     �U     �U     �U     
V     V     *V     GV  *   gV  )   �V  <   �V  D   �V  4   >W  6   sW     �W  �   �W  �   }X  �   ?Y    �Y  p   �Z  ,   h[     �[  9   �[  
   �[     �[  ]   \  >   e\  '   �\  �   �\  +   �]  
   �]     �]  �   
^  >  �^  �   2`  X   �`  *   +a  `   Va     �a     �a     �a     �a     b  
   *b  "   5b     Xb     ob     �b     �b      �b     �b  +   �b  +   c     8c     Gc     Pc     gc     vc     �c     �c     �c  (   �c     �c  >   �c     .d  
   Ed  (   Pd     yd  
   �d     �d     �d     �d     �d     �d     e  
   e      e  )   >e  )   he  
   �e  *   �e  !   �e     �e     �e  
   f     f     -f     If     ef  
   nf  
   yf  0   �f  2   �f     �f     �f     g     g     6g     Ig  +   bg  
   �g     �g     �   6       �   7   f   �   3   j   m   O              W           @           X   $   B       9   �      x   ~   w           4   E       [   i   -       *   c      ,   v   �   ^   D                    V          �       |             �       5   �           �   Q       "           A   d   �               !   L         U       �   �   l   _   0             p   G       Z   �          ]       n   M   �   '          �       \       y   H   C   
       e       #   :   F   I           r   &   �   %   �                   �   �   J          k   P   a   �   �   }   u       `   ?       >      2   /   <   Y       h       z          K   s                  b          =   {       .   �   o         t   	          )              S   �   R   N           q   T       �   �           1   g      +           8   ;   (    
*Action for the list of objects.*

#### Request parameters

1. **"app"**     - name of the application, for example: "users";
2. **"model"**   - model name of the application, for example: "user";
3. **"action"**  - action, example: "delete";
4. **"list_pk"** - list object keys of model;
5. **"confirm"** - flag confirm, if need;

#### Returned object

If confirmed, or the confirmation is not required:
`Boolean`

If not confirmed, and if confirmation is required, then transferred to
the hierarchical list of objects and a confirmation message, example:

`{
'message': 'All the objects will be deleted. You really want to do this?',
'objects': [
    <object1>,
    [<object2>, [<nested_2.1>, <nested_2.2>]],
    [<object3>, [
        [<nested_3.1>, [<nested_3.1.1>, <nested_3.1.2>]],
        [<nested_3.2>, [<nested_3.2.1>, <nested_3.2.2>]],
        ...
    ]],
}`

 
*Deleting an object.*

#### Request parameters

1. **"app"**     - name of the application, for example: "users";
2. **"model"**   - model name of the application, for example: "user";
3. **"pk"**      - the key of the object model;
4. **"confirm"** - flag confirm the removal;

#### Returned object
If confirmed, or the confirmation is not required:
`Boolean`

If not confirmed, then transferred to the list of dependent objects
that are removed together with this object.

 
*Getting a list of available devices.*

#### Request parameters
Nothing

#### Returned object
list of available devices

 
*Object creation.*

#### Request parameters

1. **"app"**    - name of the application, for example: "users";
2. **"model"**  - model name of the application, for example: "user";
3. **"fields"** - dictionary fields;

#### Возвращаемый объект
`{ object }`

 
*Reads from the database and returns an object.*

#### Request parameters

1. **"app"**    - name of the application, for example: "users";
2. **"model"**  - model name of the application, for example: "user";
3. **"pk"**     - the key of the object model;

#### Returned object
`{ object }`

 
*Returns a list of objects.*

If the object is not specified, returns a list of model objects.
Otherwise returns related objects composition or field for a specified,
a specific object.

#### Request parameters

1. **"app"**        - name of the application, for example: "users";
2. **"model"**      - model name of the application, for example: "user";
3. **"pk"**         - the key of the object model, the default == None;
4. **"foreign"**    - object field with a foreign key (fk, m2m, o2o)
                      whose objects must be returned, the default == None;
5. **"component"**  - name relationship to the model ComponentBWP,
                      objects which must be returned,
                      by default == None;

6. **"page"**       - page number, the default == 1;
7. **"per_page"**   - the number on the page, the default determined by
                      the model;
8. **"query"**      - search query, if there is;
9. **"ordering"**   - sorting objects, if different from the default;
10. **"fields_search"** - field objects to find, if different from the
                          default;
11. **"filters"**       - additional filters if there are;

#### Returned object
`{
    'count': 2,
    'end_index': 2,
    'has_next': false,
    'has_other_pages': false,
    'has_previous': false,
    'next_page_number': 2,
    'num_pages': 1,
    'number': 1,
    'object_list': [
        {
            'pk': 1,
            '__unicode__': 'First object',
            'first_name': 'First',
            ...
        },
        {
            'pk': 2,
            '__unicode__': 'Second object',
            'first_name': 'Second',
            ...
        }
    ],
    'previous_page_number': 0,
    'start_index': 1
}`

 
*Returns a summary of the data set.*

If the object is not specified, it returns the object model.
Otherwise returns for the composition of the object.

#### Request parameters

1. **"app"**        - name of the application, for example: "users";
2. **"model"**      - model name of the application, for example: "user";
3. **"pk"**         - the key of the object model, the default == None;
4. **"component"**  - name relationship to the model ComponentBWP,
                      objects which must be returned,
                      by default == None;
5. **"query"**      - search query, if there is;
6. **"ordering"**   - sorting objects, if different from the default;
7. **"fields_search"** - field objects to find, if different from the
                         default;
8. **"filters"**       - additional filters if there are;

#### Returned object
`{
    'total_sum': 2000.00,
    'total_avg': 200.00,
    'discount_sum': 100.00,
    'discount_avg': 10.00,
}`

 
*Returns the application schema formed for a specific user.*

#### Request parameters
Nothing

#### Returned object
Object (dict) of scheme

 
*The execution of commands on the device.*

#### Request parameters

1. **"device"**  - device ID;
2. **"command"** - command(method) of device;
3. **"params"**  - parameters for command (default == {});

#### Returned object
the result of the command

 
*Update the object's fields.*

#### Request parameters

1. **"app"**    - name of the application, for example: "users";
2. **"model"**  - model name of the application, for example: "user";
3. **"pk"**     - the key of the object model;
3. **"fields"** - dictionary fields for update;

#### Returned object
`{ object }`

 %(document)s from %(date)s Access denied Administration Administrators Applications Attention! You get the error! Automatic field BIK Business Web Platform Change my password Change password Confirm password: Content types Documentation E-mail address: Enter new password Error in parameters for the method Error! Example project Excuse, the page isn't found. Exit Fast development of online business applications Forgotten your password? Enter your e-mail address below, and we'll e-mail instructions for setting a new one. Functions Home INN Install another Internal error of the server. It happened for the reason that Your browser has not passed testing, insecure and does not meet modern technical requirements. JSON value KPP List fileds is blank! Log in Log in again Log out LogEntry Object Managers Name of company New document New password New password: OGRN Old password Operators Password Password (again) Password change Password change successful Password reset Password reset complete Password reset confirmation Password reset successful Password reset unsuccessful Platform Please correct the error below. Please correct the errors below. Please enter a correct username and password. Note that both fields are case-sensitive. Please enter your new password twice so we can verify you typed it in correctly. Please enter your old password, for security's sake, and then enter your new password twice so we can verify you typed it in correctly. Please go to the following page and choose a new password: Reset my password Select object Set your code for video on the www.youtube.com Sites Thank You Thanks for spending some quality time with the Web site today. Thanks for using our site! The %(site_name)s team The password reset link was invalid, possibly because it has already been used.  Please request a new password reset. This account is inactive. Username Users We've e-mailed you instructions for setting your password to the e-mail address you submitted. You should be receiving it shortly. You're receiving this e-mail because you requested a password reset for your user account at %(site_name)s. Your Web browser doesn't appear to have cookies enabled. Cookies are required for logging in. Your password has been set.  You may go ahead and log in now. Your password was changed. Your username, in case you've forgotten: about about organization about person action flag action time address administration authentication certificate code code organ code organization of issue content types cor/account correspondent account created date date and time deleted email email address file first name for the work done full title identification code of bank image issue issue of document jabber label last name license log entries log entry message middle name number number of document object id object repr organ organization of issue parent path path phones series series of document set/account settlement account site sites skype temporarily upload file temporarily upload files title title of bank type type of document updated user user settings videocode web site Project-Id-Version: BWP
Report-Msgid-Bugs-To: 
POT-Creation-Date: 2014-01-01 22:09+1100
PO-Revision-Date: 2013-01-29 01:26+1100
Last-Translator: Grigoriy Kramarenko <root@rosix.ru>
Language: ru
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)
 
*Действие для списка объектов.*

#### Параметры запроса

1. **"app"**     - название приложения, для примера: "users";
2. **"model"**   - название модели приложения, для примера: "user";
3. **"action"**  - действие, для примера: "delete";
4. **"list_pk"** - список ключей объектов модели;
5. **"confirm"** - флаг подтверждения, в случае необходимости;

#### Возвращаемый объект

Если подтверждено, либо подтверждение не требуется:
`Boolean`

Если не подтверждено, и требуется подтверждение, то передаётся
иерархический список объектов и сообщение подтверждения, для примера:

`{
'message': 'Все объекты будут удалены. Вы действительно хотите это сделать?',
'objects': [
    <object1>,
    [<object2>, [<nested_2.1>, <nested_2.2>]],
    [<object3>, [
        [<nested_3.1>, [<nested_3.1.1>, <nested_3.1.2>]],
        [<nested_3.2>, [<nested_3.2.1>, <nested_3.2.2>]],
        ...
    ]],
}`

 
*Удаление объекта.*

#### Параметры запроса

1. **"app"**     - название приложения, для примера: "users";
2. **"model"**   - название модели приложения, для примера: "user";
3. **"pk"**      - ключ объекта модели;
4. **"confirm"** - флаг подтверждения удаления;

#### Возвращаемый объект
Если подтверждено, или подтверждение не требуется:
`Boolean`

Если не подтверждено, то передаётся список зависимых объектов
которые будут удалены вместе с указанным.

 
*Получение списка доступных устройств.*

#### Параметры запроса
Пусто

#### Возвращаемый объект
список доступных устройств

 
*Создание объекта.*

#### Параметры запроса

1. **"app"**    - название приложения, для примера: "users";
2. **"model"**  - название модели приложения, для примера: "user";
3. **"fields"** - словарь полей;

#### Возвращаемый объект
`{ object }`

 
*Считывает из базы данных и возвращает объект.*

#### Параметры запроса

1. **"app"**    - название приложения, для примера: "users";
2. **"model"**  - название модели приложения, для примера: "user";
3. **"pk"**     - ключ объекта модели;

#### Возвращаемый объект
`{ object }`

 
*Возвращает список объектов.*

Если объект не указан, то возвращает список объектов модели.
В противном случае возвращает связанные объекты композиции или поля
для указанного объекта.

#### Параметры запроса

1. **"app"**        - название приложения, для примера: "users";
2. **"model"**      - название модели приложения, для примера: "user";
3. **"pk"**         - ключ объекта модели, the default == None;
4. **"foreign"**    - поле объекта с внешним ключом (fk, m2m, o2o)
                      объекты которого должны быть возвращены,
                      по умолчанию == None;
5. **"component"**  - имя отношения к модели ComponentBWP,
                      объекты которого должны быть возвращены,
                      по-умолчанию == None;

6. **"page"**       - номер страницы, по-умолчанию == 1;
7. **"per_page"**   - количество на странице, по-умолчанию определяется
                      моделью;
8. **"query"**      - поисковый запрос, если есть;
9. **"ordering"**   - сортировка объектов, если отлично от умолчания;
10. **"fields_search"** - поля объектов для поиска,
                          если отлично от умолчания;
11. **"filters"**       - дополнительные фильтры, если есть;

#### Возвращаемый объект
`{
    'count': 2,
    'end_index': 2,
    'has_next': false,
    'has_other_pages': false,
    'has_previous': false,
    'next_page_number': 2,
    'num_pages': 1,
    'number': 1,
    'object_list': [
        {
            'pk': 1,
            '__unicode__': 'Первый объект',
            'first_name': 'Первый',
            ...
        },
        {
            'pk': 2,
            '__unicode__': 'Второй объект',
            'first_name': 'Второй',
            ...
        }
    ],
    'previous_page_number': 0,
    'start_index': 1
}`

 
*Возвращает итоги для набора данных.*

Если объект не указан, то возвращает список объектов модели.
В противном случае возвращает связанные объекты композиции объекта.

#### Параметры запроса

1. **"app"**        - название приложения, для примера: "users";
2. **"model"**      - название модели приложения, для примера: "user";
3. **"pk"**         - ключ объекта модели, по-умолчанию == None;
4. **"component"**  - имя отношения к модели ComponentBWP,
                      объекты которого должны быть возвращены,
                      по-умолчанию == None;
5. **"query"**      - поисковый запрос, если есть;
6. **"ordering"**   - сортировка объектов, если отлично от умолчания;
7. **"fields_search"** - поля объектов для поиска,
                          если отлично от умолчания;
8. **"filters"**       - дополнительные фильтры, если есть;

#### Возвращаемый объект
`{
    'total_sum': 2000.00,
    'total_avg': 200.00,
    'discount_sum': 100.00,
    'discount_avg': 10.00,
}`

 
*Возвращает схему приложения, сформированную для конкретного пользователя.*

#### Параметры запроса
Пусто

#### Возвращаемый объект
Объект (dict) схемы

 
*Выполнение команд на устройстве.*

#### Параметры запроса

1. **"device"**  - идентификатор устройства;
2. **"command"** - команда(метод) устройства;
3. **"params"**  - параметры для команды (по-умолчанию == {});

#### Возвращаемый объект
результат команды

 
*Обновление полей объекта.*

#### Параметры запроса

1. **"app"**    - название приложения, для примера: "users";
2. **"model"**  - название модели приложения, для примера: "user";
3. **"pk"**     - ключ объекта модели;
3. **"fields"** - словарь полей для обновления;

#### Возвращаемый объект
`{ object }`

 %(document)s от %(date)s Доступ запрещён Администрирование Администраторы Приложения Внимание! Вы получили ошибку! Автоматическое поле БИК Бизнес Вэб-Платформа Изменить мой пароль Изменить пароль Подтвердите пароль: Типы контента Документация Адрес электронной почты: Введите новый пароль: Ошибка в параметрах для метода Ошибка! Пример проекта Извините, страница не найдена. Выход Быстрая разработка онлайн-приложений для бизнеса Забыли пароль? Введите свой адрес электронной почты ниже, и мы вышлем вам инструкцию, как установить новый пароль. Функции Начало ИНН Установить другой Внутренняя ошибка сервера. Это произошло по причине того, что Ваш браузер не прошёл тестирование, небезопасен и не отвечает современным техническим требованиям. значение JSON КПП Список полей пуст! Войти Войти снова Выйти Запись в журнале Менеджеры Название компании Новый документ Новый пароль Новый пароль: ОГРН Старый пароль Операторы Пароль Пароль (еще раз) Изменение пароля Пароль успешно изменен Восстановление пароля Восстановление пароля завершено Подтверждение восстановления пароля Пароль успешно восстановлен Ошибка восстановления пароля Платформа Пожалуйста, исправьте ошибку ниже. Пожалуйста, исправьте ошибки ниже. Пожалуйста, исправьте ошибки ниже. Пожалуйста, введите корректное имя пользователя и пароль. Помните, что оба поля чувствительны к регистру. Пожалуйста, введите новый пароль дважды, чтобы мы могли убедиться в правильности написания. В целях безопасности, пожалуйста, введите свой старый пароль, затем введите новый пароль дважды, чтобы мы могли убедиться в правильности написания. Пожалуйста, перейдите на эту страницу и введите новый пароль: Восстановить мой пароль Выберите объект Установите код видео с www.youtube.com Сайты Спасибо Благодарим вас за время, проведенное на этом сайте. Спасибо, что используете наш сайт! Команда сайта %(site_name)s Неверная ссылка для восстановления пароля. Возможно, ей уже воспользовались. Пожалуйста, попробуйте восстановить пароль еще раз. Этот аккаунт неактивен. Логин Пользователи Мы отправили инструкцию по восстановлению пароля на адрес электронной почты, который вы указали. Вы должны ее вскоре получить. Вы получили это письмо, потому что вы (или кто-то другой) запросили восстановление пароля от учётной записи на сайте %(site_name)s, которая связана с этим адресом электронной почты. В ваше Веб-браузере, кажется, не включены файлы cookie. Cookies необходимы для входа в систему. Ваш пароль был сохранен.  Теперь вы можете войти. Ваш пароль был изменен. Ваше имя пользователя (на случай, если вы его забыли): описание об организации о персоне тип действия время действия адрес администрирование авторизация свидетельство код код органа код органа выдачи типы контента корреспондентский счёт корреспондентский счёт создано дата дата и время удалено эл.почта адрес e-mail файл имя за выполненную работу полное название банковский идентификационный код изображение выдан дата выдачи документа джаббер метка фамилия лицензия записи в журнале запись в журнале сообщение отчество номер номер документа идентификатор объекта представление объекта орган орган выдачи документа родительский путь путь телефоны серия серия документа расчётный счёт расчётный счёт сайт сайты скайп временно загружаемый файл временно загружаемые файлы название название банка тип тип документа обновлено пользователь настройки пользователя видео web сайт 