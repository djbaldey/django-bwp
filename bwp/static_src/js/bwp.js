/* bwp.js for BWP
###############################################################################
# Copyright 2013 Grigoriy Kramarenko.
###############################################################################
# This file is part of BWP.
#
#    BWP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    BWP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with BWP.  If not, see <http://www.gnu.org/licenses/>.
#
# Этот файл — часть BWP.
#
#   BWP - свободная программа: вы можете перераспространять ее и/или
#   изменять ее на условиях Стандартной общественной лицензии GNU в том виде,
#   в каком она была опубликована Фондом свободного программного обеспечения;
#   либо версии 3 лицензии, либо (по вашему выбору) любой более поздней
#   версии.
#
#   BWP распространяется в надежде, что она будет полезной,
#   но БЕЗО ВСЯКИХ ГАРАНТИЙ; даже без неявной гарантии ТОВАРНОГО ВИДА
#   или ПРИГОДНОСТИ ДЛЯ ОПРЕДЕЛЕННЫХ ЦЕЛЕЙ. Подробнее см. в Стандартной
#   общественной лицензии GNU.
#
#   Вы должны были получить копию Стандартной общественной лицензии GNU
#   вместе с этой программой. Если это не так, см.
#   <http://www.gnu.org/licenses/>.
###############################################################################
*/

////////////////////////////////////////////////////////////////////////
//                   КОНСТАНТЫ И ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ                //
////////////////////////////////////////////////////////////////////////
var NEWOBJECTKEY = 'newObject',
    FIELD = null,
    delay = null,
    ACTION_WAIT = null,
    FILTER_TYPES = [
        ['exact',       'Равно',            1],
        ['gt',          'Больше',           1],
        ['gte',         'Больше или равно', 1],
        ['lt',          'Меньше',           1],
        ['lte',         'Меньше или равно', 1],

        ['range',       'Диапазон',         2],
        ['in',          'Список',           99],

        ['icontains',   'Содержит',         1],
        ['istartswith', 'Начинается',       1],
        ['iendswith',   'Заканчивается',    1],

        ['isnull',      'Пусто',            0],
        ['blank',       'Пустая строка',    0],
    ]

// Глобальные хранилища-регистраторы
window.TEMPLATES = {}; // Шаблоны
window.REGISTER  = {}; // Регистр приложений, моделей, композиций и объектов

////////////////////////////////////////////////////////////////////////
//                            НАСТРОЙКИ                               //
////////////////////////////////////////////////////////////////////////

/* Настройки шаблонизатора underscore.js в стиле Django */
_.templateSettings = {
    interpolate: /\{\{(.+?)\}\}/g,
    evaluate: /\{\%(.+?)\%\}/g, 
};

/* Включение Underscore.string методов в пространство имён Underscore */
_.mixin(_.str.exports());

////////////////////////////////////////////////////////////////////////
//                               ОБЩИЕ                                //
////////////////////////////////////////////////////////////////////////

/* Проверка объекта на пустоту */
function isEmpty(obj) {
    for (var k in obj) {
        return false; // если цикл хоть раз сработал, то объект не пустой => false
    };
    // дошли до этой строки - значит цикл не нашёл ни одного свойства => true
    return true;
};

/* Единая, переопределяемая задержка для действий или функций */
delay = (function(){
    if (DEBUG) {console.log('function:'+'delay')};
    var timer = 0;
    return function(callback, ms){
        clearTimeout (timer);
        timer = setTimeout(callback, ms);
    };
})();

/* Генератор идентификаторов, которому можно задавать статические
 * начало и конец идентификатора, например:
 *  >> id = generatorID()
 *  >> "i1363655293735"
 *  >> id = generatorID(null, "object")
 *  >> "gen1363655293736_object"
 *  >> id = generatorID("object")
 *  >> "object_i1363655293737"
 *  >> id = generatorID("model", "object")
 *  >> "model_i1363655293738_object"
 */
function generatorID(prefix, postfix) {
    if (DEBUG) {console.log('function:'+'generatorID')};
    var result = [],
        gen = 'i',
        m = 1000,
        n = 9999,
        salt = Math.floor( Math.random() * (n - m + 1) ) + m;
    gen += $.now() + String(salt);
    if (prefix) { result.push(prefix)};
    result.push(gen); 
    if (postfix) { result.push(postfix) };
    return validatorID(result);
};

/* Приводит идентификаторы в позволительный jQuery вид.
 * В данном приложении он заменяет точки на "-".
 * На вход может принимать список или строку
 */
function validatorID(id) {
    if ($.type(id) === 'array') { id = id.join('_'); };
    if (DEBUG) { console.log('function:'+'validatorID'); };
    return id.replace(/[\.,\:,\/, ,\(,\),=,?]/g, "-");
};

/* Общие функции вывода сообщений */
function handlerHideAlert() {
    if (DEBUG) {console.log('function:'+'handlerHideAlert')};
    $('.alert').alert('close');
    $('#alert-place').css('z-index', '-1000');
};
function handlerShowAlert(msg, type, callback, timeout) {
    if (DEBUG) {console.log('function:'+'handlerShowAlert')};
    timeout = timeout || 5000;
    console.log(msg);
    if (!type) { type = 'alert-error'; };
    html = TEMPLATES.alert({ msg: msg, type: type });
    $('#alert-place').css('z-index', '1000').html(html);
    $(window).scrollTop(0);
    $('.alert').alert();
    if (callback) { delay(callback, timeout); }
    else { delay(handlerHideAlert, timeout); };
    return false;
};

/* Общая функция для работы с django-quickapi */
function jsonAPI(args, callback, to_console, sync, timeout) {
    if (DEBUG) {console.log('function:'+'jsonAPI')};
    if (!args) { args = { method: "get_settings" } };
    if (!callback) { callback = function(json, status, xhr) {} };
    var jqxhr = $.ajax({
        type: "POST",
        async: !sync,
        timeout: timeout || AJAX_TIMEOUT,
        url: BWP_API_URL,
        data: {'jsonData': $.toJSON(args)},
        dataType: 'json'
    })
    // Обработка ошибок протокола HTTP
    .fail(function(xhr, status, err) {
        // Если есть переадресация, то выполняем её
        if (xhr.getResponseHeader('Location')) {
            location = xhr.getResponseHeader('Location')
            .replace(/\?.*$/, "?next=" + window.location.pathname);
            window.location.replace(location);
            console.log("1:" + xhr.getResponseHeader('Location'));
        } else {
            // Иначе извещаем пользователя ответом и в консоль
            console.log("ERROR:" + xhr.responseText);
            if (xhr.responseText) {
                handlerShowAlert(_(xhr.responseText).truncate(255), 'alert-error');
            };
        };
    })
    // Обработка полученных данных
    .done(function(json, status, xhr) {
        if (to_console) { if (DEBUG) {console.log(to_console)}; };
        /* При переадресации нужно отобразить сообщение на некоторое время,
         * а затем выполнить переход по ссылке, добавив GET-параметр для
         * возврата на текущую страницу
         */
        if ((json.status >=300) && (json.status <400) && (json.data.Location != undefined)) {
            redirect = function() {
                location = json.data.Location
                .replace(/\?.*$/, "?next=" + window.location.pathname);
                window.location.replace(location);
            }
            if (json.message) {
                handlerShowAlert(json.message, 'alert-error', redirect);
            }
            else { redirect() }
        }
        /* При ошибках извещаем пользователя полученным сообщением */
        else if (json.status >=400) {
            handlerShowAlert(json.message, 'alert-error');
        }
        /* При нормальном возврате в debug-режиме выводим в консоль
         * сообщение
         */
        else {
            if (DEBUG) {console.log($.toJSON(json.message))};
            return callback(json, status, xhr);
        };
    });
    return jqxhr
};

////////////////////////////////////////////////////////////////////////
//                             "КЛАССЫ"                               //
////////////////////////////////////////////////////////////////////////

/* класс: Настройки
 * Пример использования:
========================================================================
if (SETTINGS.init().ready) {
    SETTINGS.server['obj_on_page'] = 10
    SETTINGS.local['color'] = '#FFFFFF'
    SETTINGS.callback = function() { alert('after save') }
    SETTINGS.save()
    // либо так:
    // callback_X = function() { alert('after save') }
    // SETTINGS.save(callback_X)
};
========================================================================
* запустится callback и сбросится атрибут SETTINGS.callback
* на дефолтный (undefined), если callback.__not_reset_after__ не определён.
* .init(callback_Y) - используется только один раз, а для переполучения данных
* и если это действительно необходимо, используйте .reload(callback_Y)
* Функции "callback" - необязательны.
*/
function classSettings(default_callback) {
    this.meta = {};
    /* Установка ссылки на свой объект для вложенных функций */
    self = this;
    /* Проверка возможности исполнения */
    if ((typeof localStorage == 'undefined')
                                || (typeof $.evalJSON == 'undefined')){
        return {}; 
    };

    _unique_key = SETTINGS_UNIQUE_KEY;

    /* Настройки по-умолчанию */
    _server = {}; // непосредственный объект хранения
    _local = { tabs:[], filters:{}, };  // непосредственный объект хранения
    _values = { 'server': _server, 'local': _local }; // ссылки на хранилища

    /* Пока с сервера не получены данные */
    _values_is_set = false;
    _responseServer = null;

    /* Атрибут SETTINGS.ready - показывает готовность */
    this.__defineGetter__('ready', function() { return _values_is_set; });

    /* В этом атрибуте можно задавать функцию, которая будет исполняться
     * всякий раз в конце методов: save() и reload(),
     * а также при первичной инициализации, обащаясь к all, server, local
     * При этом функция может не перезаписываться на умолчальную после
     * её исполнения, для этого в callback нужен положительный атрибут
     * __not_reset_after__
     */
    _callback = default_callback; // functions
    _run_callback = function() {
        if (_callback === "function") {
            _callback();
            if (!_callback.__not_reset_after__) {
                _callback = default_callback;
            };
        };
    };

    this.callback = _callback;

    /* Дата последнего сохранения на сервере */
    _last_set_server = null; // Date()
    this.last_set = _last_set_server;

    /* Дата последнего получения с сервера */
    _last_get_server = null; // Date()
    this.last_get = _last_get_server;

    /* Метод получения данных из localStorage и ServerStorage */
    _init = function(callback) {
        if (callback) { _callback = callback; };
        _values_is_set = false;
        _local = $.evalJSON(localStorage.getItem(_unique_key)) || _local;
        _get_server();
        return self;
    };
    /* Публичный метод */
    this.init = _init;

    /* Принудительное получение данных изо всех хранилищ */
    this.reload = _init;

    /* Проверка первичной инициализации */
    _check_init = function() {
        if (!_values_is_set) { _init(); };
        return self;
    };

    /* Публичные атрибуты краткого, облегчённого доступа к данным хранилищ.
     * Включают проверку первичной инициализации.
     * Атрибут SETTINGS.all - все настройки
     */
    this.__defineGetter__('all', function() { _check_init(); return _values; });
    /* Атрибут SETTINGS.server - настройки ServerStorage */
    this.__defineGetter__('server', function() { _check_init(); return _server; });
    /* Атрибут SETTINGS.local - настройки localStorage */
    this.__defineGetter__('local', function() { _check_init(); return _local; });

    /* Сохранение в localStorage и ServerStorage. Вторым аргументом можно
     * передавать какую именно настройку ('server' или 'local') требуется
     * сохранить.
     */
    this.save = function(callback, only) {
        if (callback) { _callback = callback; };
        if (only != 'local') {
            _set_server(); // Сначала на сервер,
        };
        if (only != 'server') { // затем в локалсторадж
            localStorage.setItem(_unique_key, $.toJSON(self.local));
        };
        _run_callback(); // RUN CALLBACK IF EXIST!!!
        return self;
    };

    this.save_server = function(callback) { return self.save(callback, 'server'); };
    this.save_local  = function(callback) { return self.save(callback, 'local'); };

    /* Загрузка настроек в ServerStorage.
     * Асинхронный метод, просто отправляем на сервер данные,
     * не дожидаясь результата.
     * Но если данные не будут сохранены на сервере, то в браузере
     * появится сообщение об ошибке (обработка ошибок в протоколе 
     * django-quickapi) через jsonAPI(). Подразумевается, что это позволит
     * работать при нестабильных соединениях.
     */
    _set_server = function() {
        sync = false;
        _responseServer = null;
        args = { method: "set_settings", settings: self.server };
        cb = function(json, status, xhr) {
            if (!json.data) { handlerShowAlert(json.message) }
            else {
                _last_set_server = new Date();
                _responseServer = json;
            };
        };
        jqxhr = new jsonAPI(args, cb, 'SETTINGS.set_server() call jsonAPI()', sync);
        return [_last_set_server, _responseServer, jqxhr];
    };

    /* Получение настроек из ServerStorage.
     * Синхронный метод, на котором все события браузера останавливаются
     */
    _get_server = function() {
        sync = true;
        _responseServer = null;
        args = { method: "get_settings" };
        cb = function(json, status, xhr) {
            _server = json.data;
            _last_get_server = new Date();
            _responseServer = json;
            _values_is_set = true;
            _run_callback(); // RUN CALLBACK IF EXIST!!!
        };
        jqxhr = new jsonAPI(args, cb, 'SETTINGS.get_server() call jsonAPI()', sync);
        return [_last_get_server, _responseServer, jqxhr];
    };

    // Очистка от null в списке вкладок
    this.cleanTabs = function() {
        _tabs = [];
        $.each(_local.tabs, function(i, item) {
            if (item) { _tabs.push(item); }
        });
        _local.tabs = _tabs;
        return self;
    };
};

/* класс: Приложение BWP */
function classApp(data) {
    this.has_module_perms = data.has_module_perms;
    this.name = data.name;
    this.id = validatorID(this.name);
    this.label = data.label;
    this.title = 'Приложение:'+ this.label;
    _models = [];
    this.models = _models;
    // Init
    app = this;
    $.each(data.models, function(index, item) {
        _models.push(new classModel(app, item));
    });
    // Register
    REGISTER[this.id] = this;
};

/* класс: Модель BWP */
function classModel(app, data) {
    this.template = TEMPLATES.layoutModel;
    this.app   = app;
    this.perms = data.perms;
    this.meta  = data.meta;
    this.name  = data.name;
    this.model = this.name;
    this.id    = validatorID(this.model);
    this.label = data.label;
    this.title = this.app.label +': '+ this.label;
    this.query = null;
    this.fix = {};
    this.paginator = null;
    _collection_reports     = [];
    this.collection_reports = _collection_reports;
    _object_reports     = [];
    this.object_reports = _object_reports;
    _composes     = {};
    this.composes = _composes;
    _actions = {};
    this.actions = _actions;
    model = this;
    // Init
    if (data.meta.compositions) {
        $.each(data.meta.compositions, function(index, item) {
            _composes[item.meta.related_name] = item;
        });
    };
    if (data.meta.reports) {
        $.each(data.meta.reports, function(index, item) {
            if (item.for_object) {
                _object_reports.push(item);
            } else {
                _collection_reports.push(item);
            };
        });
        if (this.collection_reports.length <1) {
            this.collection_reports = null;
        };
        if (this.object_reports.length <1) {
            this.object_reports = null;
        };
    };
    //~ console.log(this.collection_reports)
    //~ console.log(this.object_reports)
    // Register
    if ((!this.meta) || (!this.meta.list_display)) {
        console.log("Модель не может быть зарегистрирована.")
    } else {
        REGISTER[this.id] = this;
    };
};

/* класс: Модель для выбора (в неё копируется настоящая модель)*/
function classSelector(model, multiple) {
    $.extend(true, this, model);
    this.id = validatorID([this.id, 'selector']);
    this.template = TEMPLATES.layoutSelector;
    // Запрещаем все действия.
    this.perms = { 'delete': false, 'add': false, 'change': false };
    this.actions = null;
    this.meta.list_display = this.meta.list_display.slice(0,1);
    this.meta.list_per_page = 5;
    this.multiple = multiple ? true : false;
    selector = this;
    // Init
    // Register
    REGISTER[this.id] = this;
    // method
    this.get_checked_items = function() {
        _checkboxes = $(
            '#collection_'
            + this.id
            +' tbody td:nth-child(1) input[type=checkbox]:checked'
        );
        return _checkboxes;
    };
};

/* класс: Композиция */
function classCompose(object, data) {
    this.template = TEMPLATES.layoutCompose;
    this.object     = object;
    this.editable = Boolean(this.object.pk);
    this.perms    = data.perms;
    this.name     = data.name;
    this.meta     = data.meta;
    this.compose  = this.meta.related_name;
    this.model    = this.meta.related_model;
    this.is_m2m   = this.meta.is_many_to_many;
    this.id    = validatorID([this.object.id, this.name, this.compose]);
    this.label = data.label;
    this.title = this.object.label +': '+ this.label;
    this.query = null;
    this.fix = {};
    this.m2m_fix = [];
    this.m2m_fixaction = null;
    this.paginator = null;
    _actions = {};
    this.actions = _actions;
    compose = this;
    // Init
    // Register
    REGISTER[this.id] = this;
};

/* класс: Объект */
function classObject(data) {
    this.template = TEMPLATES.layoutObject;
    this.model = REGISTER[validatorID(data.model)];
    this.pk    = data.pk;
    this.id    = this.pk ? validatorID(data.model+'.'+this.pk)
                         : generatorID(NEWOBJECTKEY);
    this.__unicode__ = this.pk ? data.__unicode__
                               : 'Новый объект ('+this.model.label+')';
    this.label       = this.__unicode__;
    this.title = this.model.label +': '+ this.label;
    _properties     = data.properties;
    this.properties = _properties;
    _fields     = data.fields;
    this.fields = _fields;
    this.get_fields = function() {
        L = {};
        $.each(this.model.meta.fields, function(i, item) {
            L[item] = _fields[item];
        });
        return L;
    };
    this.get_column_value = function(colname) {
        if (colname in _fields) {
            return _fields[colname];
        }
        else if (colname in _properties) {
            return _properties[colname];
        };
        return '';
    };
    _composes = [];
    this.composes = _composes;
    this.widgets = this.model.meta.widgets;
    this.actions = this.model.actions;
    this.fix = {};
    this.fixaction = null;
    object = this;
    // Init
    if (this.model.composes) {
        $.each(this.model.composes, function(rel_name, item) {
            _composes.push(new classCompose(object, item));
        });
    };
    // register
    REGISTER[this.id] = this;
};

////////////////////////////////////////////////////////////////////////
//                      ОБЩИЕ ОБРАБОТЧИКИ "КЛАССОВ"                   //
////////////////////////////////////////////////////////////////////////

// Процедуры

/* Применение изменений на сервере для объектов в моделях и композициях */
function handlerCommitInstance(instance, done) {
    if (DEBUG) {console.log('function:'+'handlerCommitInstance')};
    //~ is_changed = false;
    _objects = []
    _model = instance.model; // по-умолчанию для экземпляра объекта
    
    appendObject = function(obj) {
        /* Функция оперирует только экземплярами класса classObject */
        //~ if ((!isEmpty(obj.fix)) || (obj.fixaction == 'delete')) {
            $.extend(true, obj.fields, obj.fix);
            _objects.push(
                {   pk: obj.pk,
                    fields: obj.fields,
                    model: obj.model.name,
                    action: obj.fixaction,
                    fix: obj.fix,
                }
            );
        //~ };
    };
    /* При сохранении композиции, на самом деле сохраняем модель
     * (modelBWP), но объекты сохранения берутся из композиции.
     */ 
    if ((instance instanceof classModel) || (instance instanceof classCompose)) {
        _model = instance;
        $.each(instance.fix, function(key, val) {
            appendObject(val);
        });
    } else { appendObject(instance); };

    /* Формируем запрос на сервер */
    args = {
        "method"  : "commit",
        "objects" : _objects,
    };
    cb = function(json, status, xhr) {
        handlerCollectionGet(_model);
        if (done) { done() };
    };
    jqxhr = new jsonAPI(args, cb, 'handlerCommitInstance(instance) call jsonAPI()', true, 300000);
    return jqxhr;
};

/* Применение изменений на сервере для m2m-композиций */
function handlerCommitComposeM2M(compose, done) {
    if (DEBUG) {console.log('function:'+'handlerCommitComposeM2M')};

    /* Формируем запрос на сервер */
    args = {
        "method"  : "m2m_commit",
        "model"   : compose.object.model.name,
        "pk"      : compose.object.pk,
        "compose" : compose.compose,
        "action"  : compose.m2m_fixaction,
        "objects" : compose.m2m_fix,
    };
    cb = function(json, status, xhr) {
        handlerCollectionGet(compose);
        if (done) { done() };
    };
    jqxhr = new jsonAPI(args, cb, 'handlerCommitComposeM2M(compose, done) call jsonAPI()');
    return jqxhr;
};

/* Отрисовка макета модели, композиции или объекта */
function handlerLayoutRender(instance, just_prepare) {
    if (DEBUG) {console.log('function:'+'handlerLayoutRender')};
    //~ console.log(instance);
    html = instance.template({data:instance});
    if (!just_prepare) {
        $('#layout_'+instance.id).html(html);
        // Одиночные биндинги на загрузку коллекций объекта
        if (instance instanceof classObject) {
            $('#layout_'+instance.id+' button[data-loading=true]')
            .one('click', eventLayoutLoad);
        };
    };
    return html;
};

/* Загружает необходимый макет модели или объекта */
function handlerLayoutLoad(instance) {
    if (DEBUG) {console.log('function:'+'handlerLayoutLoad')};
    html = handlerLayoutRender(instance);
    // Загрузка коллекции
    if ((instance instanceof classModel) || (instance instanceof classCompose)) {
        jqxhr = handlerCollectionGet(instance);
    };
};

// События

/* Обработчик события загрузки макета */
function eventLayoutLoad() {
    if (DEBUG) {console.log('function:'+'eventLayoutLoad')};
    data = $(this).data();
    instance = REGISTER[data.id];
    handlerLayoutLoad(instance);
    // Удаление атрибута загрузки
    $(this).removeAttr("data-loading");
    return true;
};

/* Обработчик события выбора всех строк в таблице модели, композиции,
 * селектора */
function handlerSelectAllToggle() {
    $table = $(this).parents('table');
    $inputs = $table.find("tbody td:nth-child(1) input[type=checkbox]");
    checked = this.checked;
    $.each($inputs, function(i, item) { item.checked = checked });
};

/* Обработчик события клика на строке в таблице модели, композиции,
 * селектора */
function eventRowClick() {
    if (DEBUG) {console.log('function:'+'eventRowClick')};
    $this = $(this);
    $this.addClass('info').siblings('tr').removeClass('info');
    return true;
};

////////////////////////////////////////////////////////////////////////
//                             КОЛЛЕКЦИИ                              //
////////////////////////////////////////////////////////////////////////

// Процедуры

/* Отрисовка коллекций моделей и композиций */
function handlerCollectionRender(instance, just_prepare) {
    if (DEBUG) {console.log('function:'+'handlerCollectionRender')};
    if (instance instanceof classObject) {  
        return '';
    };
    html = TEMPLATES.collection({data:instance});
    if (!just_prepare) {
        $('#collection_'+instance.id).html(html);
    };
    return html;
};

/* Функция получает коллекцию с сервера и перерисовывает цель
 * коллекции модели/композиции, для которых она вызывалась
 */
function handlerCollectionGet(instance) {
    if (DEBUG) {console.log('function:'+'handlerCollectionGet')};
    var _filters = [];
    if (instance.filters) {
        $.each(instance.filters, function(i, item) {
            _filters.push({
                active:  item.active,
                field:   item.field,
                type:    item.type,
                inverse: item.inverse,
                values:  item.values,
                field_title:   item.field_title,
                type_title:   item.type_title,
            })
        });
    };
    args = {
        "method"  : "get_collection",
        "model"   : instance.model,
        "compose" : instance.compose       || null,
        "order_by": instance.meta.ordering || null,
        "fields":   instance.meta.search_fields || null,
        "filters":  _filters,
    };
    args[instance.meta.search_key] = instance.query || null;
    if (instance.object) {
        args["pk"] = instance.object.pk || 0;
    };
    if (instance.paginator) {
        args["page"]    = instance.paginator.page     || 1;
        args["per_page"]= instance.paginator.per_page || null;
    };
    cb = function(json, status, xhr) {
        instance.paginator = json.data;
        html = handlerCollectionRender(instance);
    };
    jqxhr = new jsonAPI(args, cb, 'handlerCollectionGet() call jsonAPI()');
    return jqxhr;
};

// События

/* Обработчик события поиска по коллекции */
function eventCollectionSearch() {
    if (DEBUG) {console.log('function:'+'eventCollectionSearch')};
    search         = this;
    data           = $(search).data();
    instance       = REGISTER[data['id']];
    instance.query = $(search).val() || null;
    wrap = function() { return handlerCollectionGet(instance); };
    jqxhr          = delay(wrap, 500);
    return jqxhr;
};

/* Обработчик события обновления поиска по коллекции */
function eventCollectionSearchRefresh() {
    if (DEBUG) {console.log('function:'+'eventCollectionSearchRefresh')};
    search         = $(this).siblings('input[data-action=collection_search][data-id='+ $(this).data().id +']');
    data           = $(search).data();
    instance       = REGISTER[data['id']];
    instance.query = $(search).val() || null;
    jqxhr          = handlerCollectionGet(instance);
    return jqxhr;
};

/* Обработчик события установки размера коллекции на странице */
function eventCollectionCount() {
    if (DEBUG) {console.log('function:'+'eventCollectionCount')};
    data     = $(this).data();
    instance = REGISTER[data['id']];
    if (instance.paginator) {
        instance.paginator.page = 1;
        instance.paginator.per_page = $(this).val()
            || $(this).data()['count']
            || instance.meta.list_per_page;
        $('[data-placeholder=collection_count][data-id='+instance.id+']')
            .text(instance.paginator.per_page);
    };
    jqxhr = handlerCollectionGet(instance);
    return jqxhr;
};

/* Обработчик события паджинации коллекции */
function eventCollectionPage() {
    if (DEBUG) {console.log('function:'+'eventCollectionPage')};
    data     = $(this).data();
    instance = REGISTER[data['id']];
    if (instance.paginator) {
        instance.paginator.page = $(this).val() || $(this).data()['page'] || 1;
    };
    jqxhr = handlerCollectionGet(instance);
    return jqxhr;
};


////////////////////////////////////////////////////////////////////////
//                               ОБЪЕКТЫ                              //
////////////////////////////////////////////////////////////////////////

// Процедуры

/* Добавление объекта */
function handlerObjectAdd(instance) {
    if (DEBUG) {console.log('function:'+'handlerObjectAdd')};
    args = {
        "method"  : "get_object",
        "model"   : instance.name,
        "pk"      : null,
        "filler"  : {},
    };
    console.log(instance);
    if (instance instanceof classCompose) {
        
        args.filler[instance.meta.related_field] = instance.object.pk;
    };
    cb = function(json, status, xhr) {
        object = new classObject(json.data);
        object.fixaction = 'add';
        object.model.fix[object.id] = object;
        handlerTabOpen(object);
    };
    jqxhr = new jsonAPI(args, cb, 'handlerObjectAdd(model) call jsonAPI()');
    return jqxhr;
};

/* Загрузка файла */
function handlerTempUploadFile(object, field) {
    if (DEBUG) {console.log('function:'+'handlerTempUploadFile')};

    var formData = new FormData(),
        file = field.files[0],
        xhr = new XMLHttpRequest();

    if (!file) {
        object.fix[field.name] = 0;
        return true;
    }
    else {

        formData.append('file', file);

        xhr.open('POST',
            '/upload/'+ object.model.name +'/',
            true
        );
        xhr.onload = function(e) {
            json = JSON.parse(this.response);
            object.fix[field.name] = json.data;
            $(field).siblings('button[name]').text(file.name)
                .attr('title', file.name);
        };
        xhr.send(formData);  // multipart/form-data

        return true;
    };
};

/* Изменение объекта добавлением полей во временное хранилище */
function handlerObjectChange(object, $field) {
    if (DEBUG) {console.log('function:'+'handlerObjectChange')};
    var name  = $field.attr('name'),
        type  = $field.attr('type'),
        value = $field.val();
    if (type) { type = type.toLowerCase(); };
    if (type in {'file':0, 'image':0}) {
        handlerTempUploadFile(object, $field[0]);
    } else if ($.type(object.fields[name]) === 'array') {
        value = [value, $field.text()];
    } else if ($.type(object.fields[name]) === 'boolean') {
        value = $field.is(':checked');
    };
    object.fix[name] = value;
    object.fixaction = object.fixaction || 'change';
    object.model.fix[object.id] = object;
};

/* Копирование объекта */
function handlerObjectCopy(data, clone) {
    if (DEBUG) {console.log('function:'+'handlerObjectCopy')};
    if (data.id) {
        object = REGISTER[data.id];
        data = {};
        data.model = object.model.name;
        data.pk    = object.pk;
    };
    args = {
        "method"  : "get_object",
        "model"   : data.model,
        "pk"      : data.pk,
        "copy"    : true,
        "clone"    : clone,
    };
    cb = function(json, status, xhr) {
        object = new classObject(json.data);
        object.fixaction = 'add';
        object.model.fix[object.id] = object;
        handlerTabOpen(object);
    };
    jqxhr = new jsonAPI(args, cb, 'handlerObjectCopy(data, clone) call jsonAPI()');
};

/* Удаление объекта */
function handlerObjectDelete(data, done) {
    if (DEBUG) {console.log('function:'+'handlerObjectDelete')};
    args = {
        "method"  : "commit",
        "objects" : [
            {   pk    : data.pk,
                fields: {},
                model : data.model,
                action: 'delete'
            }
        ],
    };
    cb = function(json, status, xhr) {
        handlerCollectionGet(REGISTER[validatorID(data.model)]);
        if (done) { done() };
    };
    jqxhr = new jsonAPI(args, cb, 'handlerObjectDelete(data, done) call jsonAPI()', true, 180000);
};

/* Функция мутирования строки объекта */
function handlerObjectRowMuted(object) {
    if (DEBUG) {console.log('function:'+'handlerObjectRowMuted')};
    $('tr[data-model="'+object.model.name+'"][data-pk="'+object.pk+'"]')
        .addClass('muted');
};

/* Функция удаления мутирования строки объекта */
function handlerObjectRowUnmuted(object) {
    if (DEBUG) {console.log('function:'+'handlerObjectRowUnmuted')};
    $('tr[data-model="'+object.model.name+'"][data-pk="'+object.pk+'"]')
        .removeClass('muted');
};

// События

/* Обработчик события открытия объекта */
function eventObjectOpen() {
    if (DEBUG) {console.log('function:'+'eventObjectOpen')};
    $this = $(this);
    data = $this.data();
    if (!data.model) { return false };
    object = REGISTER[data.id];
    if (object) {
        handlerTabOpen(object);
        return null;
    };
    args = {
        "method"  : "get_object",
        "model"   : data.model,
        "pk"      : data.pk || null,
    };
    cb = function(json, status, xhr) {
        object = new classObject(json.data);
        $this.data('id', object.id);
        handlerTabOpen(object);
    };
    jqxhr = new jsonAPI(args, cb, 'eventObjectOpen() call jsonAPI()');
    return jqxhr;
};

/* Обработчик события создания объекта */
function eventObjectAdd(event) {
    if (DEBUG) {console.log('function:'+'eventObjectAdd')};
    var $this = $(this),
        data = $this.data(),
        instance = REGISTER[data.id],
        m2m = instance.is_m2m ? instance : null;
    if ((m2m) && (event) && (event.data) && (event.data.m2m)) {
        handlerM2MSelect(m2m);
        return true;
    };

    handlerObjectAdd(instance);
    return true;
};

/* Обработчик события копирования объекта */
function eventObjectCopy() {
    if (DEBUG) {console.log('function:'+'eventObjectCopy')};
    $this = $(this);
    data = $this.data();
    handlerObjectCopy(data);
    return true;
};

/* Обработчик события полного копирования объекта */
function eventObjectClone() {
    if (DEBUG) {console.log('function:'+'eventObjectClone')};
    $this = $(this);
    data = $this.data();
    handlerObjectCopy(data, true);
    return true;
};

/* Обработчик события удаления объекта */
function eventObjectDelete(event) {
    if (DEBUG) {console.log('function:'+'eventObjectDelete')};
    done = undefined;
    $this = $(this);
    data = $this.data();
    if ((event) && (event.data) && (event.data.m2m)) {
        compose = REGISTER[data.id];
        compose.m2m_fix = [data.pk];
        compose.m2m_fixaction = 'delete';
        handlerCommitComposeM2M(compose);
        return true;
    };
    object = REGISTER[data.id];
    if (object instanceof classObject) {
        data.model = object.model.name;
        data.pk    = object.pk;
        done = function() { handlerTabClose(object) }
    };
    text = "<b>Вы действительно желаете удалить этот объект?</b><br>"
          +"<i>Удаление невозможно обратить, если этот объект не рассчитан"
          +" на перемещение в корзину.</i>"
    handlerModalShowSubmit(text, handlerObjectDelete, data, done);
    return true;
};

/* Обработчик события изменения объекта */
function eventObjectChange() {
    if (DEBUG) {console.log('function:'+'eventObjectChange')};
    $this = $(this);
    data = $this.data();
    object = REGISTER[data.id];
    handlerObjectChange(object, $this);
    return true;
};

/* Обработчик события восстановления объекта */
function eventObjectReset() {
    if (DEBUG) {console.log('function:'+'eventObjectReset')};
    $this = $(this);
    data = $this.data();
    object = REGISTER[data.id];
    object.fix = {};
    handlerLayoutRender(object);
    return true;
};

/* Обработчик события удаления объекта */
function eventObjectSave() {
    if (DEBUG) {console.log('function:'+'eventObjectSave')};
    $this = $(this);
    data = $this.data();
    object = REGISTER[data.id];
    handlerCommitInstance(object, function() { handlerTabClose(object); } );
    return true;
};

/* Обработчик события выбора объекта */
function eventObjectSelect() {
    if (DEBUG) {console.log('function:'+'eventObjectSelect')};
    $this = $(this);
    data = $this.data();
    FIELD.val(data.pk).text(data.unicode).attr('title', data.unicode)
        .change().siblings('button[disabled]').removeAttr('disabled');
    $('#modal').modal('hide');
    return true;
};

////////////////////////////////////////////////////////////////////////
//                              СЕЛЕКТОРЫ                             //
////////////////////////////////////////////////////////////////////////

// Процедуры

/* Обработчик события запуска выбора для m2m полей */
function handlerM2MSelect(m2m) {
    if (DEBUG) {console.log('function:'+'handlerM2MSelect')};
    model = REGISTER[validatorID(m2m.name)]
    var selector = new classSelector(model, true),
        mhead = 'Выберите требуемые объекты',
        mbody = handlerLayoutRender(selector, true),
        mfoot = null,
        data  = {},
        buttons = [
            {model: model, action:'object_add',      label:'Новый',    css:'btn-warning'},
            {model: null,  action:'modal_close',     label:'Закрыть',  css:''},
            {model: m2m,   action:'selector_append', label:'Добавить', css:'btn-info'},
            {model: m2m,   action:'selector_submit', label:'Выбрать',  css:'btn-primary'},
        ];
    data = { buttons:buttons, selector: selector };
    //~ console.log(data);
    mfoot = TEMPLATES.modalFooter({ mfoot:data, });
    //~ console.log(mfoot);
    handlerModalShow(mhead, mbody, mfoot,
        function() {handlerCollectionGet(selector)}
    );
};

/* Обработчик события запуска выбора */
function handlerFieldSelect($field) {
    if (DEBUG) {console.log('function:'+'handlerFieldSelect')};
    FIELD = $field;
    data = $field.data();
    object = REGISTER[data.id];
    model =  REGISTER[validatorID(data.model)];
    selector = new classSelector(model);
    mhead = 'Выберите требуемый объект';
    mbody = handlerLayoutRender(selector, true);
    mfoot = null;
    handlerModalShow(mhead, mbody, mfoot,
        function() {handlerCollectionGet(selector)}
    );
};

/* Обработчик добавления значений в набор */
function handlerSelectorSubmit(compose, selector) {
    if (DEBUG) {console.log('function:'+'handlerSelectorSubmit')};
    _objects = [];
    checked = selector.get_checked_items();
    $.each(checked, function(i, item) {
        data = $(item).data();
        _objects.push(data.pk);
    });
    compose.m2m_fix = _objects;
    compose.m2m_fixaction = 'add';
    handlerCommitComposeM2M(compose);
};

// События

/* Обработчик события удаления значения в поле выбора */
function eventFieldClear(event) {
    if (DEBUG) {console.log('function:'+'eventFieldClear')};
    $this = $(this);
    $this.attr('disabled', 'disabled');
    // Обработка сброса выбора файла
    if ((event) && (event.data) && (event.data.file)) {
        $field = $this.siblings('input[name]');
        $field.val(null).change();
    };
    // Обработка сброса кнопки с названием (и значением)
    $this.siblings('button[name]').val(null).html('&nbsp;')
        .attr('title', '').change();
    return true;
};

/* Обработчик события выбора значения */
function eventFieldSelect(event) {
    if (DEBUG) {console.log('function:'+'eventFieldSelect')};
    $this = $(this);
    // Обработка вызова выбора файла
    if ((event) && (event.data) && (event.data.file)) {
        $this.siblings('input[name]').click();
    }
    // Обработка вызова селекторов
    else {
        $field = $this.siblings('button[name]');
        handlerFieldSelect($field);
    };
    return true;
};

/* Обработчик события добавления значений в набор с последующим
 * закрытием окна, если это требуется
 */
function eventSelectorSubmit(event) {
    if (DEBUG) {console.log('function:'+'eventSelectorSubmit')};
    $this = $(this);
    data = $this.data();
    compose  = REGISTER[data.id];
    selector = REGISTER[validatorID([compose.name, 'selector'])];
    handlerSelectorSubmit(compose, selector);
    if (event.data.close) { handlerModalHide() };
    return true;
};

////////////////////////////////////////////////////////////////////////
//                           МОДАЛЬНОЕ ОКНО                           //
////////////////////////////////////////////////////////////////////////

function handlerModalShowSubmit(text, wait, arg1, arg2, arg3, arg4) {
    if (DEBUG) {console.log('function:'+'handlerModalShowSubmit')};
    var mhead = 'Подтверждение',
        mbody = text,
        mfoot = TEMPLATES.modalFooter({ mfoot: {} });
    ACTION_WAIT = function() { wait(arg1, arg2, arg3, arg4); };
    handlerModalShow(mhead, mbody, mfoot);
};

/* Обработчик формирования и запуска модального окна */
function handlerModalShow(mhead, mbody, mfoot, done) {
    if (DEBUG) {console.log('function:'+'handlerModalShow')};
    $modal = $('#modal');
    modal = {};
    modal.mhead = mhead;
    modal.mbody = mbody;
    modal.mfoot = mfoot;
    html = TEMPLATES.modal({modal:modal});
    $modal.html(html).modal('show');
    if (done) { done() };
};

/* Обработчик закрытия модального окна */
function handlerModalHide(done) {
    if (DEBUG) {console.log('function:'+'handlerModalHide')};
    $modal = $('#modal');
    $modal.modal('hide');
    if (done) { done() };
};

////////////////////////////////////////////////////////////////////////
//                               МЕНЮ                                 //
////////////////////////////////////////////////////////////////////////

// Процедуры

function handlerMenuAppLoad() {
    if (DEBUG) {console.log('function:'+'handlerMenuAppLoad')};
    sync = true;
    args = { method: "get_apps" };
    cb = function(json, status, xhr) {
        apps = [];
        $.each(json.data, function(index, item) {
            apps.push(new classApp(item));
        });
        html = TEMPLATES.menuApp({data:apps});
        $('#menu-app ul[role=menu]').html(html);
        $('#menu-app').show();
    };
    jqxhr = new jsonAPI(args, cb, 'handlerMenuAppLoad() call jsonAPI()', sync);
    return jqxhr;
};

////////////////////////////////////////////////////////////////////////
//                              ВКЛАДКИ                               //
////////////////////////////////////////////////////////////////////////

// Процедуры

/* Открывает вкладку на рабочей области */
function handlerTabOpen(data) {
    if (DEBUG) {console.log('function:'+'handlerTabOpen')};
    handlerObjectRowMuted(data);

    tab = $('#main-tab #tab_'+ data.id);
    if (tab.length > 0) {
        // Отображаем вкладку
        tab.find('a').tab('show');
    } else {
        // Контент вкладки
        html = TEMPLATES.layoutDefault({data: data});
        $('#main-tab-content').append(html);
        // Сама вкладка
        html = TEMPLATES.tab({data: data});
        $('#main-tab').append(html);
        // Отображаем вкладку c небольшой задержкой
        delay(function() {
            $('#main-tab a:last').tab('show').click();
        }, 1);
        // Добавляем вкладку в хранилище, если её там нет
        // (т.к. эту же функцию использует восстановление сессии). 
        if ((data.id.indexOf(NEWOBJECTKEY) == -1)
            &&($.inArray(data.id, SETTINGS.local.tabs) < 0)
            &&($('#menu-app li[class!=disabled] a[data-id='+data.id+']').size() >0)) {
            SETTINGS.local.tabs.push(data.id);
            SETTINGS.save_local();
        };
        // Устанавливаем одиночный биндинг на загрузку контента при щелчке на вкладке
        $('#tab_'+data.id+' a').one('click', eventLayoutLoad);
    };
    return true;
};

/* Закрывает вкладку, удаляя её с рабочей области и из настроек */
function handlerTabClose(data) {
    if (DEBUG) {console.log('function:'+'handlerTabClose')};
    id = data ? data.id : null;
    $('#tab_'+id).remove();
    $('#layout_'+id).remove();
    instance = REGISTER[id];
    if (instance) {
        handlerObjectRowUnmuted(instance);
        if (instance instanceof classObject) {
            $.each(instance.composes, function(i, item) {
                delete REGISTER[item.id]
            });
            delete REGISTER[id];
        };
    };
    // Удаляем из хранилища информацию об открытой вкладке
    num = $.inArray(id, SETTINGS.local.tabs);
    if (num > -1) {
        delete SETTINGS.local.tabs[num];
        SETTINGS.cleanTabs().save_local();
    };
    // открываем последнюю вкладку
    $('#main-tab a:last').click();
};

/* Восстанавливает вкладки, открытые до обновления страницы */
function handlerTabRestore() {
    if (DEBUG) {console.log('function:'+'handlerTabRestore')};
    $.each(SETTINGS.local.tabs, function(i, item) {
        // только приложения в меню
        $('#menu-app li[class!=disabled] a[data-id='+item+']').click();
    });
};

// События

/* Обработчик события открытия вкладки */
function eventTabOpen() {
    if (DEBUG) {console.log('function:'+'eventTabOpen')};
    data = $(this).data();
    data = REGISTER[data.id] || data;
    handlerTabOpen(data);
    return true;
};

/* Обработчик события закрытия вкладки */
function eventTabClose() {
    if (DEBUG) {console.log('function:'+'eventTabClose')};
    data = $(this).data();
    data = REGISTER[data.id] || data;
    handlerTabClose(data);
    return true;
};

////////////////////////////////////////////////////////////////////////
//                              ФИЛЬТРЫ                               //
////////////////////////////////////////////////////////////////////////

/* Обработчик заргузки сохранённых фильтров для моделей и коллекций */
function handlerFiltersFromSettings() {
    if (DEBUG) {console.log('function:'+'handlerFiltersFromSettings')};
    if (!SETTINGS.local.filters) {return false;};
    $.each(SETTINGS.local.filters, function(key, val) {
        var instance = REGISTER[key];
        instance.filters = val;
    });
    return true;
};

/* Обработчик отображения фильтров*/
function handlerFiltersRender(instance) {
    if (DEBUG) {console.log('function:'+'handlerFiltersRender')};
    if (instance instanceof classObject) {  
        return false;
    };
    html = TEMPLATES.filters({data:instance});
    $('#collection_filters_'+instance.id).html(html);
    return html;
};

/* Обработчик события показа-сокрытия фильтров */
function eventFilters() {
    if (DEBUG) {console.log('function:'+'eventFilters')};
    var data = $(this).data(),
        instance = REGISTER[data.id];
    if ($('#collection_filters_'+data.id+' table').size() >0) {
        $('#collection_filters_'+data.id).html('');
        var _filters = [];
        $.each(instance.filters, function(index, item) {
            if (item.field && item.type && item.values) {
                _filters.push(item);
            };
        });
        instance.filters = _filters;
    } else {
        handlerFiltersRender(instance);
    }
    return true;
};

/* Обработчик добавления фильтра */
function handlerFilterAppend(instance) {
    if (DEBUG) {console.log('function:'+'handlerFilterAppend')};
    if (instance instanceof classObject) {  
        return false;
    };
    firstfield = instance.meta.filters[0] ? instance.meta.filters[0].field
                                          : null;
    if (!firstfield) {
        handlerShowAlert('Не установлены поля для фильтров.');
        return false;
    };
    newfilter = {
        type:        null,
        inverse:     false,
        active:      false, 
        field:       null,
        values:      null,
        field_title: null,
        type_title:  null,
    };
    if (!instance.filters) { instance.filters = []; };
    instance.filters.push(newfilter);
    html = TEMPLATES.filter({data:instance, item:newfilter});
    $('#collection_filters_'+instance.id+' table tbody').append(html);
    return html;
};

/* Обработчик события добавления фильтра */
function eventFilterAppend() {
    if (DEBUG) {console.log('function:'+'eventFilterAppend')};
    var data = $(this).data(),
        instance = REGISTER[data.id];
    handlerFilterAppend(instance);
    return true;
};

/* Обработчик события удаления фильтра */
function eventFilterRemove() {
    if (DEBUG) {console.log('function:'+'eventFilterRemove')};
    var data = $(this).data(),
        instance = REGISTER[data.id],
        index = data.filter_index;
    instance.filters.splice(index, index+1);
    $('#collection_filters_'+instance.id+' tr[data-filter_index='+index+']')
        .remove();
    handlerCollectionGet(instance);

    if (!SETTINGS.local.filters) { SETTINGS.local.filters = {}; };
    SETTINGS.local.filters[instance.id] = instance.filters
    SETTINGS.save(null, 'local')

    return true;
};

/* Обработчик события изменения поля фильтра */
function eventFilterChangeField() {
    if (DEBUG) {console.log('function:'+'eventFilterChangeField')};
    var data = $(this).data(),
        instance = REGISTER[data.id],
        index = data.filter_index,
        val = $(this).val();
        text = $(this).find('[value='+val+']').text();
    instance.filters[index].field = val;
    instance.filters[index].field_title = text;
    handlerFilterChangeActive(instance, index, false);
    $('#collection_filters_'+instance.id+
        ' [data-place=filter_values][data-filter_index='+index+']')
        .html('');
    if (!val) {
        // блокировка всех прочих
        $('#collection_filters_'+instance.id+
            ' [data-action=filter_change_active][data-filter_index='+index+']')
            .attr('disabled', 'disabled');
        $('#collection_filters_'+instance.id+
            ' [data-action=filter_change_type][data-filter_index='+index+']')
            .attr('disabled', 'disabled');
        $('#collection_filters_'+instance.id+
            ' [data-action=filter_change_inverse][data-filter_index='+index+']')
            .attr('disabled', 'disabled');
        $('#collection_filters_'+instance.id+
            ' [data-place=filter_values][data-filter_index='+index+']')
            .html('');
        return true;
    };
    $('#collection_filters_'+instance.id+
        ' [data-action=filter_change_type][data-filter_index='+index+']')
        .removeAttr('disabled');
    return true;
};


/* Обработчик события изменения типа фильтра */
function eventFilterChangeType() {
    if (DEBUG) {console.log('function:'+'eventFilterChangeType')};
    var data = $(this).data(),
        instance = REGISTER[data.id],
        index = data.filter_index,
        val = $(this).val();
        text = $(this).find('[value='+val+']').text();
    instance.filters[index].type = val;
    instance.filters[index].type_title = text;
    handlerFilterChangeActive(instance, index, false);
    if (!val) {
        // блокировка всех прочих

        $('#collection_filters_'+instance.id+
            ' [data-action=filter_change_active][data-filter_index='+index+']')
            .attr('disabled', 'disabled');
        $('#collection_filters_'+instance.id+
            ' [data-action=filter_change_inverse][data-filter_index='+index+']')
            .attr('disabled', 'disabled');
        $('#collection_filters_'+instance.id+
            ' [data-place=filter_values][data-filter_index='+index+']')
            .html('');
        handlerCollectionGet(instance);
        return true;
    };

    $('#collection_filters_'+instance.id+
        ' [data-action=filter_change_active][data-filter_index='+index+']')
        .removeAttr('disabled');
    $('#collection_filters_'+instance.id+
        ' [data-action=filter_change_inverse][data-filter_index='+index+']')
        .removeAttr('disabled');

    //~ console.log(instance);
    var html = TEMPLATES.filter_values({data:instance, index:index }),
        $values = $('#collection_filters_'+instance.id+
            ' [data-place=filter_values][data-filter_index='+index+']');

    if (instance.filters[index].type != 'blank') {
        $values.html(html);
        if (instance.filters[index].type == 'range') { $values.append(html);};
    };

    return true;
};

/* Обработчик изменения активности фильтра */
function handlerFilterChangeActive(instance, index, active) {
    if (DEBUG) {console.log('function:'+'handlerFilterChangeActive')};
    instance.filters[index].active = active;
    //~ console.log(instance);
    //~ var $active = $('#collection_filters_'+instance.id+
        //~ ' [data-action=filter_change_active][data-filter_index='+index+']');
    return true;
};

/* Обработчик события изменения активности фильтра */
function eventFilterChangeActive() {
    if (DEBUG) {console.log('function:'+'eventFilterChangeActive')};
    var data = $(this).data(),
        instance = REGISTER[data.id],
        index = data.filter_index,
        checked = !$(this).hasClass('active');
    handlerFilterChangeValues(instance, index);
    handlerFilterChangeActive(instance, index, checked);
    if (checked) {
        $('#collection_filters_'+instance.id+
            ' [data-action=filter_change_field][data-filter_index='+index+']')
            .attr('disabled', 'disabled');
        $('#collection_filters_'+instance.id+
            ' [data-action=filter_change_type][data-filter_index='+index+']')
            .attr('disabled', 'disabled');
    } else {
        $('#collection_filters_'+instance.id+
            ' [data-action=filter_change_field][data-filter_index='+index+']')
            .removeAttr('disabled');
        $('#collection_filters_'+instance.id+
            ' [data-action=filter_change_type][data-filter_index='+index+']')
            .removeAttr('disabled');
    };
    handlerCollectionGet(instance);
    return true;
};

/* Обработчик изменения инверсии фильтра */
function handlerFilterChangeInverse(instance, index, inverse) {
    if (DEBUG) {console.log('function:'+'handlerFilterChangeInverse')};
    instance.filters[index].inverse = inverse;
    return true;
};

/* Обработчик события изменения инверсии фильтра */
function eventFilterChangeInverse() {
    if (DEBUG) {console.log('function:'+'eventFilterChangeInverse')};
    var data = $(this).data(),
        instance = REGISTER[data.id],
        index = data.filter_index,
        checked = !$(this).hasClass('active');
    handlerFilterChangeInverse(instance, index, checked);
    if (instance.filters[index].active) {
        handlerCollectionGet(instance);
    };
    return true;
};

/* Обработчик изменения значения фильтра */
function handlerFilterChangeValues(instance, index) {
    if (DEBUG) {console.log('function:'+'handlerFilterChangeValues')};

    var $place = $('#collection_filters_'+instance.id+
        ' [data-place=filter_values][data-filter_index='+index+']'),
        $values = $place.find('[data-action=filter_change_values]');
    instance.filters[index].values = [];
    instance.filters[index].values_html = $place.html();

    //~ $('#collection_filters_'+instance.id+
        //~ ' [data-action=filter_change_active][data-filter_index='+index+']')
        //~ .removeClass('active');

    if (!SETTINGS.local.filters) { SETTINGS.local.filters = {}; };
    SETTINGS.local.filters[instance.id] = instance.filters;
    SETTINGS.save(null, 'local');

    $.each($values, function(i, item) {
        instance.filters[index].values.push($(item).val());
    });

    return true;
};

/* Обработчик события изменения значения фильтра */
function eventFilterChangeValues() {
    if (DEBUG) {console.log('function:'+'eventFilterChangeValues')};
    var data = $(this).data(),
        instance = REGISTER[data.id],
        index = data.filter_index,
        val = $(this).val();

    if (val) {
        $(this).attr('value', val);
    };

    handlerFilterChangeActive(instance, index, false);
    handlerFilterChangeValues(instance, index);

    if (instance.filters[index].active) {
        handlerCollectionGet(instance);
    };
    return true;
};

/* Обработчик добавления поля значения фильтра */
function handlerFilterAppendValue(instance, index) {
    if (DEBUG) {console.log('function:'+'handlerFilterAppendValue')};
    var html = TEMPLATES.filter_values({data:instance, index:index }),
        $values = $('#collection_filters_'+instance.id+
            ' [data-place=filter_values][data-filter_index='+index+']');
    $values.append(html);
    return true;
};

/* Обработчик события добавления поля значения фильтра */
function eventFilterAppendValue() {
    if (DEBUG) {console.log('function:'+'eventFilterAppendValue')};
    var data = $(this).data(),
        instance = REGISTER[data.id],
        index = data.filter_index;
    handlerFilterAppendValue(instance, index);
    $(this).remove();

    return true;
};


////////////////////////////////////////////////////////////////////////
//                              ОТЧЁТЫ                                //
////////////////////////////////////////////////////////////////////////

/* Обработчик события выбора отчёта коллекции */
function eventCollectionPrint() {
    if (DEBUG) {console.log('function:'+'eventCollectionPrint')};
    var data = $(this).data(),
        instance = REGISTER[data.id],
        sync = true,
        args = {
            method: "get_collection_report_url",
            report: data.report,
            model   : instance.model,
            query   : instance.query,
            order_by: instance.order_by,
            fields  : instance.fields,
            filters : instance.filters,
        },
        cb = function(json, status, xhr) {
            var url = json.data;
            window.open(url, '_blank');
        };
    jqxhr = new jsonAPI(args, cb, 'eventCollectionPrint() call jsonAPI()', sync);
    return true;
};

/* Обработчик события выбора отчёта объекта */
function eventObjectPrint() {
    if (DEBUG) {console.log('function:'+'eventObjectPrint')};
    var data = $(this).data(),
        object = REGISTER[data.id],
    sync = true;
    args = {
        method: "get_object_report_url",
        model : data.model,
        pk    : data.pk,
        report: data.report,
    };
    cb = function(json, status, xhr) {
        var url = json.data;
        window.open(url, '_blank');
    };
    jqxhr = new jsonAPI(args, cb, 'eventObjectPrint() call jsonAPI()', sync);
    return true;
};

////////////////////////////////////////////////////////////////////////
//                              ПРОЧЕЕ                                //
////////////////////////////////////////////////////////////////////////

/* Обработчик события отмены ожидаемого действия */
function eventWaitCancel() {
    if (DEBUG) {console.log('function:'+'eventWaitCancel')};
    ACTION_WAIT = null
    return true;
};

/* Обработчик события подтверждения ожидаемого действия */
function eventWaitSubmit() {
    if (DEBUG) {console.log('function:'+'eventWaitSubmit')};
    ACTION_WAIT()
    ACTION_WAIT = null
    return true;
};


/* Обработчик установки шаблонов */
function handlerTemplates() {
    if (DEBUG) {console.log('function:'+'handlerTemplates')};

    TEMPLATES.alert             = _.template($('#underscore-alert').html());
    TEMPLATES.menuApp           = _.template($('#underscore-menu-app').html());
    TEMPLATES.collection        = _.template($('#underscore-collection').html());
    TEMPLATES.layoutModel       = _.template($('#underscore-layout-model').html());
    TEMPLATES.layoutSelector    = _.template($('#underscore-layout-selector').html());
    TEMPLATES.layoutCompose     = _.template($('#underscore-layout-compose').html());
    TEMPLATES.layoutObject      = _.template($('#underscore-layout-object').html());
    TEMPLATES.layoutDefault     = _.template($('#underscore-layout-default').html());
    TEMPLATES.tab               = _.template($('#underscore-tab').html());
    TEMPLATES.modal             = _.template($('#underscore-modal').html());
    TEMPLATES.modalFooter       = _.template($('#underscore-modal-footer').html());
    TEMPLATES.filter            = _.template($('#underscore-filter').html());
    TEMPLATES.filters           = _.template($('#underscore-filters').html());
    TEMPLATES.filter_values     = _.template($('#underscore-filter-values').html());

    return true;
};

/* Обработчик установки биндингов для элементов */
function handlerBindinds() {
    if (DEBUG) {console.log('function:'+'handlerBindinds')};

    // Биндинг на сокрытие алерта
    $('body').on('click', 'button.close[data-dismiss="alert"]', 
        function () {$('#alert-place').css('z-index', '-1000');});

    $('body').on('click',  'tr[data-pk]', eventRowClick);
    // Биндинги на открытие-закрытие вкладок и их контента
    $('#menu-app li[class!=disabled]').on('click',  'a', eventTabOpen);
    $('#main-tab').on('click', 'button.close[data-id]',  eventTabClose)

    handlerTabRestore();

    // Биндинг на фильтрацию, паджинацию и количество в коллекциях
    $('body').on('keyup',  '[data-action=collection_search]', eventCollectionSearch);
    $('body').on('change', '[data-action=collection_search]', eventCollectionSearch);
    $('body').on('click',  '[data-action=collection_search_refresh]', eventCollectionSearchRefresh);
    $('body').on('click',  '[data-action=collection_count]',  eventCollectionCount);
    $('body').on('change', '[data-action=collection_page]',   eventCollectionPage);
    $('body').on('click',  '[data-action=collection_page]',   eventCollectionPage);

    // Биндинги на кнопки и ссылки
    $('body').on('click', '[data-action=object_open]',     eventObjectOpen);
    $('body').on('click', '[data-action=object_copy]',     eventObjectCopy);
    $('body').on('click', '[data-action=object_clone]',    eventObjectClone);
    $('body').on('click', '[data-action=object_add]',                 eventObjectAdd);
    $('body').on('click', '[data-action=object_add_m2m]', {m2m:true}, eventObjectAdd);
    $('body').on('click', '[data-action=object_delete]',                 eventObjectDelete);
    $('body').on('click', '[data-action=object_delete_m2m]', {m2m:true}, eventObjectDelete);
    $('body').on('keyup', '[data-action=object_change]', eventObjectChange);
    $('body').on('change','[data-action=object_change]', eventObjectChange);
    $('body').on('click', '[data-action=object_reset]',  eventObjectReset);
    $('body').on('click', '[data-action=object_save]',   eventObjectSave);
    $('body').on('click', '[data-action=object_select]', eventObjectSelect);
    $('#modal').on('click', '[data-action=selector_append]', {close:false}, eventSelectorSubmit);
    $('#modal').on('click', '[data-action=selector_submit]', {close:true},  eventSelectorSubmit);
    $('#modal').on('click', '[data-action=wait_cancel]',  eventWaitCancel);
    $('#modal').on('click', '[data-action=wait_submit]',  eventWaitSubmit);

    // Биндинги на кнопки выбора значения
    $('body').on('click', '[data-action=field_clear]',                    eventFieldClear);
    $('body').on('click', '[data-action=file_field_clear]', {file:true},  eventFieldClear);
    $('body').on('click', '[data-action=field_select]',                   eventFieldSelect);
    $('body').on('click', '[data-action=file_field_select]', {file:true}, eventFieldSelect);

    // Биндинг на чекбоксы
    $('body').on('click', '[data-toggle=checkboxes]',   handlerSelectAllToggle);

    // Биндинги на фильтры
    $('body').on('click', '[data-action=collection_filters]',   eventFilters);
    $('body').on('click', '[data-action=filter_append]',   eventFilterAppend);
    $('body').on('click', '[data-action=filter_remove]',   eventFilterRemove);
    $('body').on('click', '[data-action=filter_change_field]',   eventFilterChangeField);
    $('body').on('click', '[data-action=filter_change_type]',   eventFilterChangeType);
    $('body').on('click', '[data-action=filter_change_inverse]',   eventFilterChangeInverse);
    $('body').on('click', '[data-action=filter_change_active]',   eventFilterChangeActive);
    $('body').on('click', '[data-action=filter_change_values]',   eventFilterChangeValues);
    $('body').on('change', '[data-action=filter_change_values]',   eventFilterChangeValues);
    $('body').on('click', '[data-action=filter_append_value]',   eventFilterAppendValue);

    // Биндинги на отчёты
    $('body').on('click', '[data-action=collection_print]',   eventCollectionPrint);
    $('body').on('click', '[data-action=object_print]',   eventObjectPrint);

    return true;
};



////////////////////////////////////////////////////////////////////////
//                            ИСПОЛНЕНИЕ                              //
////////////////////////////////////////////////////////////////////////

/* Выполнение чего-либо после загрузки страницы */
$(document).ready(function($) {
    if (DEBUG) {console.log('function:'+'$(document).ready')};
    // Инициализация шаблонов Underscore
    handlerTemplates();

    // Загрузка меню
    $('#menu-app').hide();
    $('#menu-func').hide();
    handlerMenuAppLoad()

    /* Инициализируем настройки */
    window.SETTINGS = new classSettings();

    // Инициализация для Bootstrap
    $("alert").alert();
    $(".dropdown-toggle").dropdown();

    // Если настройки готовы, то запускаем все процессы
    if (SETTINGS.init().ready) {
        $('#search').focus();
        handlerBindinds();
        handlerFiltersFromSettings();
    } else {
        console.log("ОШИБКА! Загрузка настроек не удалась.");
    }
});
