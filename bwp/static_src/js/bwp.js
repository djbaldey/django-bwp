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
var NEWOBJECTKEY = 'newObject';
var FIELD = null;

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
    for (var key in obj) {
        return false; // если цикл хоть раз сработал, то объект не пустой => false
    }
    // дошли до этой строки - значит цикл не нашёл ни одного свойства => true
    return true;
}

/* Единая, переопределяемая задержка для действий или функций */
var delay = (function(){
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
    var result = [];
    var gen = 'i';
    var m = 1000;
    var n = 9999;
    var salt = Math.floor( Math.random() * (n - m + 1) ) + m;
    gen += $.now() + String(salt);
    if (prefix) { result.push(prefix)};
    result.push(gen); 
    if (postfix) { result.push(postfix) };
    return validatorID(result);
}

/* Приводит идентификаторы в позволительный jQuery вид.
 * В данном приложении он заменяет точки на "-".
 * На вход может принимать список или строку
 */
function validatorID(id) {
    if ($.type(id) === 'array') {id = id.join('_')};
    if (DEBUG) {console.log('function:'+'validatorID')};
    return id.replace(/[\.,\:,\/, ,\(,\),=,?]/g, "-");
}

/* Общие функции вывода сообщений */
function handlerHideAlert() {
    if (DEBUG) {console.log('function:'+'handlerHideAlert')};
    $('.alert').alert('close');
}
function handlerShowAlert(msg, type, callback) {
    if (DEBUG) {console.log('function:'+'handlerShowAlert')};
    console.log(msg);
    if (!type) { type = 'alert-error' }
    html = TEMPLATES.alert({ msg: msg, type: type });
    $('#alert-place').html(html);
    $(window).scrollTop(0);
    $('.alert').alert();
    if (callback) { delay(callback, 5000); }
    else { delay(handlerHideAlert, 5000); }
    return false;
}

/* Общая функция для работы с django-quickapi */
function jsonAPI(args, callback, to_console, sync) {
    if (DEBUG) {console.log('function:'+'jsonAPI')};
    if (!args) { var args = { method: "get_settings" } };
    if (!callback) { callback = function(json, status, xhr) {} };
    var jqxhr = $.ajax({
        type: "POST",
        async: !sync,
        timeout: AJAX_TIMEOUT,
        url: BWP_API_URL,
        data: 'jsonData=' + $.toJSON(args),
        dataType: 'json'
    })
    // Обработка ошибок протокола HTTP
    .fail(function(xhr, status, err) {
        // Если есть переадресация, то выполняем её
        if (xhr.getResponseHeader('Location')) {
            window.location = xhr.getResponseHeader('Location')
            .replace(/\?.*$/, "?next=" + window.location.pathname);
            console.log("1:" + xhr.getResponseHeader('Location'));
        } else {
            // Иначе извещаем пользователя ответом и в консоль
            console.log("ERROR:" + xhr.responseText);
            handlerShowAlert(_(xhr.responseText).truncate(255), 'alert-error');
        };
    })
    // Обработка полученных данных
    .done(function(json, status, xhr) {
        if (to_console) { if (DEBUG) {console.log(to_console)}; };
        /* При переадресации нужно отобразить сообщение на некоторое время,
         * а затем выполнить переход по ссылке, добавив GET-параметр для
         * возврата на текущую страницу
         */
        if ((json.status >=300) && (json.status <400) && (json.data.Location)) {
            handlerShowAlert(json.message, 'alert-error', function() {
                window.location.href = json.data.Location
                .replace(/\?.*$/, "?next=" + window.location.pathname);
            });
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
    })
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
    if (DEBUG) {console.log('function:'+'Settings')};
    /* Установка ссылки на свой объект для вложенных функций */
    self = this;
    /* Проверка возможности исполнения */
    if (typeof localStorage == 'undefined' || typeof $.evalJSON == 'undefined')
        { return {}; }

    _unique_key = SETTINGS_UNIQUE_KEY;

    /* Настройки по-умолчанию */
    _server = {}; // непосредственный объект хранения
    _local = { tabs:[], };  // непосредственный объект хранения
    _values = { 'server': _server, 'local': _local }; // ссылки на хранилища

    /* Пока с сервера не получены данные */
    _values_is_set = false;
    _responseServer = null;

    /* Атрибут SETTINGS.ready - показывает готовность */
    this.__defineGetter__('ready', function() { return _values_is_set; })

    /* В этом атрибуте можно задавать функцию, которая будет исполняться
     * всякий раз в конце методов: save() и reload(),
     * а также при первичной инициализации, обащаясь к all, server, local
     * При этом функция может не перезаписываться на умолчальную после
     * её исполнения, для этого в callback нужен положительный атрибут
     * __not_reset_after__
     */
    _callback = default_callback; // functions
    _run_callback = function() {
        if (_callback) {
            _callback();
            if (!_callback.__not_reset_after__) {
                _callback = default_callback;
            };
        };
    };

    this.callback = _callback

    /* Дата последнего сохранения на сервере */
    _last_set_server =  null; // Date()
    this.last_set = _last_set_server;

    /* Дата последнего получения с сервера */
    _last_get_server =  null; // Date()
    this.last_get = _last_get_server;

    /* Метод получения данных из localStorage и ServerStorage */
    _init = function(callback) {
        if (callback) { _callback = callback; }
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
    _check_init = function() { if (!_values_is_set) { _init(); } return self; };

    /* Публичные атрибуты краткого, облегчённого доступа к данным хранилищ.
     * Включают проверку первичной инициализации.
     * Атрибут SETTINGS.all - все настройки
     */
    this.__defineGetter__('all', function() { _check_init(); return _values; })
    /* Атрибут SETTINGS.server - настройки ServerStorage */
    this.__defineGetter__('server', function() { _check_init(); return _server; })
    /* Атрибут SETTINGS.local - настройки localStorage */
    this.__defineGetter__('local', function() { _check_init(); return _local; })

    /* Сохранение в localStorage и ServerStorage. Вторым аргументом можно
     * передавать какую именно настройку ('server' или 'local') требуется
     * сохранить.
     */
    this.save = function(callback, only) {
        if (callback) { _callback = callback; }
        if (only != 'local') {
            _set_server(); // Сначала на сервер,
        }
        if (only != 'server') { // затем в локалсторадж
            localStorage.setItem(_unique_key, $.toJSON(self.local))
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
        args = { method: "set_settings", settings: self.server }
        cb = function(json, status, xhr) {
            if (!json.data) { handlerShowAlert(json.message) }
            else {
                _last_set_server = new Date();
                _responseServer = json;
            }
        }
        jqxhr = new jsonAPI(args, cb, 'SETTINGS.set_server() call jsonAPI()', sync)
        return [_last_set_server, _responseServer, jqxhr]
    };

    /* Получение настроек из ServerStorage.
     * Синхронный метод, на котором все события браузера останавливаются
     */
    _get_server = function() {
        sync = true;
        _responseServer = null;
        args = { method: "get_settings" }
        cb = function(json, status, xhr) {
            _server = json.data;
            _last_get_server = new Date();
            _responseServer = json;
            _values_is_set = true;
            _run_callback(); // RUN CALLBACK IF EXIST!!!
            }
        jqxhr = new jsonAPI(args, cb, 'SETTINGS.get_server() call jsonAPI()', sync);
        return [_last_get_server, _responseServer, jqxhr]
    };

    // Очистка от null в списке вкладок
    this.cleanTabs = function() {
        _tabs = []
        $.each(_local.tabs, function(i, item) {
            if (item) { _tabs.push(item); }
        });
        _local.tabs = _tabs;
        return self;
    }
}

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
    _composes     = {};
    this.composes = _composes
    _widgets = [];
    this.widgets = _widgets;
    _actions = {};
    this.actions = _actions;
    model = this;
    // Init
    if (data.meta.compositions) {
        $.each(data.meta.compositions, function(index, item) {
            _composes[item.meta.related_name] = item;
        });
    }
    $.each(model.meta.list_display, function(i, name) {
        if (name == '__unicode__') {
            _widgets.push({name:name, label: model.label, attr:{}})
        } else {
            $.each(model.meta.widgets, function(ii, widget) {
                if (name == widget.name) { _widgets.push(widget) };
            });
        }
    });
    // Register
    REGISTER[this.id] = this;
};

/* класс: Модель для выбора (в неё копируется настоящая модель)*/
function classSelector(model) {
    $.extend(true, this, model);
    this.id = validatorID([this.id, 'selector'])
    this.template = TEMPLATES.layoutSelector;
    // Запрещаем все действия.
    this.perms.delete = false;
    this.perms.add = false;
    this.perms.change = false;
    //~ this.meta.list_display = this.meta.list_display.slice(0,1);
    this.meta.list_per_page = 5;
    // Register
    REGISTER[this.id] = this;
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
    this.id    = validatorID([this.object.id, this.name]);
    this.label = data.label;
    this.title = this.object.label +': '+ this.label;
    this.query = null;
    this.fix = {};
    this.paginator = null;
    _widgets = [];
    this.widgets = _widgets;
    _actions = {};
    this.actions = _actions;
    compose = this;
    // Init
    $.each(compose.meta.list_display, function(i, name) {
        if (name == '__unicode__') {
            _widgets.push({name:name, label: compose.label, attr:{}})
        } else {
            $.each(compose.meta.widgets, function(ii, widget) {
                if (name == widget.name) { _widgets.push(widget) };
            });
        }
    });
    // Register
    REGISTER[this.id] = this;
};

/* класс: Объект */
function classObject(data) {
    this.template = TEMPLATES.layoutObject;
    this.model = REGISTER[validatorID(data.model)];
    this.pk    = data.pk;
    this.id    = this.pk ? validatorID(data.model+'.'+this.pk) : generatorID(NEWOBJECTKEY);
    this.__unicode__ = data.__unicode__;
    this.label       = this.__unicode__;
    this.title = this.model.label +': '+ this.label;
    _fields     = data.fields;
    this.fields = _fields;
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
    }
    // register
    REGISTER[this.id] = this;
};

////////////////////////////////////////////////////////////////////////
//                         ФУНКЦИИ С "КЛАССАМИ"                       //
////////////////////////////////////////////////////////////////////////

/* Отрисовка коллекций моделей и композиций */
function handlerCollectionRender(instance, just_prepare) {
    if (DEBUG) {console.log('function:'+'handlerCollectionRender')};
    if (instance instanceof classObject) {  
        return '';
    }
    html = TEMPLATES.collection({data:instance})
    if (!just_prepare) {
        $('#collection_'+instance.id).html(html);
    }
    return html
}

/* Отрисовка макета модели, композиции или объекта */
function handlerLayoutRender(instance, just_prepare) {
    if (DEBUG) {console.log('function:'+'handlerLayoutRender')};
    html = instance.template({data:instance})
    if (!just_prepare) {
        $('#layout_'+instance.id).html(html)
        // Одиночные биндинги на загрузку коллекций объекта
        if (instance instanceof classObject) {
            $('#layout_'+instance.id+' button[data-loading=true]')
            .one('click', eventLayoutLoad);
        }
    }
    return html
}

/* Применение изменений на сервере */
function handlerCommitInstance(instanse) {
    if (DEBUG) {console.log('function:'+'handlerCommitInstance')};
    is_changed = false;
    _objects = []
    _model = instance.model;
    appendObject = function(obj) {
        if ((!isEmpty(obj.fix)) || (obj.fixaction == 'delete')) {
            $.extend(true, obj.fields, obj.fix);
            _objects.push(
                {   pk: obj.pk, fields: obj.fields,
                    model: obj.model.name,
                    action: obj.fixaction,
                    fix: obj.fix,
                }
            );
        }
    }
    if ((instance instanceof classModel) || (instance instanceof classCompose)) {
        _model = instance;
        $.each(instance.fix, function(key, val) {
            appendObject(val)
        });
    } else { appendObject(instance) }
    args = {
        "method"  : "commit",
        "objects" : _objects,
    }
    cb = function(json, status, xhr) {
        handlerCollectionGet(_model)
    };
    jqxhr = new jsonAPI(args, cb, 'handlerCommitInstance(instanse) call jsonAPI()')
    return jqxhr
}

/* Добавление объекта */
function handlerObjectAdd(model, $this) {
    if (DEBUG) {console.log('function:'+'handlerObjectAdd')};
    _data = {};
    _data['model']  = model.model;
    _data['fields'] = model.meta.defaults;
    _data['__unicode__'] = 'Новый объект';
    data = {};
    $.extend(true, data, _data);
    newobject = new classObject(data);
    $.extend(true, newobject.fix, newobject.fields);
    newobject.fixaction = 'add'
    newobject.model.fix[newobject.id] = newobject
    //~ $this.data('id', newobject.id);
    handlerTabOpen(newobject);
    return newobject
}

/* Изменение объекта добавлением полей во временное хранилище */
function handlerObjectChange(object, $field) {
    if (DEBUG) {console.log('function:'+'handlerObjectChange')};
    var name = $field.attr('name');
    var value = $field.val();
    if ($.type(object.fields[name]) === 'array') {
        value = [value, $field.text()];
    } else if ($.type(object.fields[name]) === 'boolean') {
        value = $field.is(':checked');
    }
    object.fix[name] = value;
    object.fixaction = object.fixaction || 'change';
    object.model.fix[object.id] = object;
}

/* Копирование объекта */
function handlerObjectCopy(object, $this) {
    if (DEBUG) {console.log('function:'+'handlerObjectCopy')};
    create = function(object) {
        _data = {};
        _data['model'] = object.model.name;
        _data['fields'] = object.fields;
        _data['__unicode__'] = object.__unicode__;
        data = {};
        $.extend(true, data, _data);
        newobject = new classObject(data);
        $.extend(true, newobject.fix, newobject.fields);
        newobject.fixaction = 'add'
        newobject.model.fix[newobject.id] = newobject
        $this.data('id', newobject.id);
        handlerTabOpen(newobject);
        return newobject
    };
    if (object) { create(object); }
    else {
        args = {
            "method"  : "get_object",
            "model"   : data.model,
            "pk"      : data.pk || null,
        }
        cb = function(json, status, xhr) {
            object = new classObject(json.data);
            newobject = create(object)
            $this.data('id', newobject.id);
            handlerTabOpen(newobject);
        }
        jqxhr = new jsonAPI(args, cb, 'handlerObjectCopy(object) call jsonAPI()')
    }
}

/* Удаление объекта */
function handlerObjectDelete(data, $this) {
    if (DEBUG) {console.log('function:'+'handlerObjectDelete')};
    args = {
        "method"  : "commit",
        "objects" : [
            {   pk: data.pk, fields: {},
                model: data.model,
                action: 'delete'
            }
        ],
    }
    cb = function(json, status, xhr) {
        handlerCollectionGet(REGISTER[validatorID(data.model)])
        }
    jqxhr = new jsonAPI(args, cb, 'handlerObjectDelete() call jsonAPI()')
}

/* Обработчик события открытия объекта */
function eventObjectOpen() {
    if (DEBUG) {console.log('function:'+'eventObjectOpen')};
    $this = $(this);
    data = $this.data();
    if (!data.model) { return false };
    object = REGISTER[data.id];
    if (object) {
        handlerTabOpen(object);
        return null
    }
    args = {
        "method"  : "get_object",
        "model"   : data.model,
        "pk"      : data.pk || null,
    }
    cb = function(json, status, xhr) {
        object = new classObject(json.data);
        $this.data('id', object.id);
        handlerTabOpen(object);
    }
    jqxhr = new jsonAPI(args, cb, 'eventObjectOpen() call jsonAPI()')
    return jqxhr
}

/* Обработчик события создания объекта */
function eventObjectAdd(event) {
    if (DEBUG) {console.log('function:'+'eventObjectAdd')};
    $this = $(this);
    data = $this.data();
    if ((event) && (event.data) && (event.data.m2m)) {
        console.log(event)
        return true
    }
    model = REGISTER[data.id];
    if (model instanceof classCompose) {
        model = REGISTER[validatorID(model.name)]
    }
    handlerObjectAdd(model, $this);
    return true;
}

/* Обработчик события копирования объекта */
function eventObjectCopy() {
    if (DEBUG) {console.log('function:'+'eventObjectCopy')};
    $this = $(this);
    data = $this.data();
    object = REGISTER[data.id];
    handlerObjectCopy(object, $this)
    return true
}

/* Обработчик события удаления объекта */
function eventObjectDelete(event) {
    if (DEBUG) {console.log('function:'+'eventObjectDelete')};
    $this = $(this);
    data = $this.data();
    if ((event) && (event.data) && (event.data.m2m)) {
        console.log(event)
        return true
    }
    object = REGISTER[data.id];
    handlerObjectDelete(data, $this);
    return true
}

/* Обработчик события изменения объекта */
function eventObjectChange() {
    if (DEBUG) {console.log('function:'+'eventObjectChange')};
    $this = $(this);
    data = $this.data();
    object = REGISTER[data.id];
    handlerObjectChange(object, $this)
    return true
}

/* Обработчик события восстановления объекта */
function eventObjectReset() {
    if (DEBUG) {console.log('function:'+'eventObjectReset')};
    $this = $(this);
    data = $this.data();
    object = REGISTER[data.id];
    object.fix = {};
    handlerLayoutRender(object);
    return true
}

/* Обработчик события удаления объекта */
function eventObjectSave() {
    if (DEBUG) {console.log('function:'+'eventObjectSave')};
    $this = $(this);
    data = $this.data();
    object = REGISTER[data.id];
    handlerCommitInstance(object);
    return true
}

/* Функция мутирования строки объекта */
function handlerObjectRowMuted(object) {
    if (DEBUG) {console.log('function:'+'handlerObjectRowMuted')};
    $('tr[data-model="'+object.model.name+'"][data-pk="'+object.pk+'"]')
        .addClass('muted');
}

/* Функция удаления мутирования строки объекта */
function handlerObjectRowUnmuted(object) {
    if (DEBUG) {console.log('function:'+'handlerObjectRowUnmuted')};
    $('tr[data-model="'+object.model.name+'"][data-pk="'+object.pk+'"]')
        .removeClass('muted');
}

/* Функция получает коллекцию с сервера и перерисовывает цель
 * коллекции модели/композиции, для которых она вызывалась
 */
function handlerCollectionGet(instance) {
    if (DEBUG) {console.log('function:'+'handlerCollectionGet')};
    args = {
        "method"  : "get_collection",
        "model"   : instance.model,
        "compose" : instance.compose       || null,
        "order_by": instance.meta.ordering || null,
    }
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
        //~ console.log(html)
    }
    jqxhr = new jsonAPI(args, cb, 'handlerCollectionGet() call jsonAPI()')
    return jqxhr
}

/* Обработчик события фильтрации коллекции */
function eventCollectionFilter() {
    if (DEBUG) {console.log('function:'+'eventCollectionFilter')};
    search         = this;
    data           = $(search).data();
    instance       = REGISTER[data['id']];
    instance.query = $(search).val() || null;
    jqxhr          = handlerCollectionGet(instance);
    return jqxhr
}

/* Обработчик события установки размера коллекции на странице */
function eventCollectionCount() {
    if (DEBUG) {console.log('function:'+'eventCollectionCount')};
    data     = $(this).data();
    instance = REGISTER[data['id']];
    if (instance.paginator) {
        instance.paginator.page = 1;
        instance.paginator.per_page = $(this).val() || $(this)
            .data()['count'] || instance.meta.list_per_page;
        $('[data-placeholder=collection_count][data-id='+instance.id+']')
            .text(instance.paginator.per_page)
    };
    jqxhr = handlerCollectionGet(instance);
    return jqxhr
}

/* Обработчик события паджинации коллекции */
function eventCollectionPage() {
    if (DEBUG) {console.log('function:'+'eventCollectionPage')};
    data     = $(this).data();
    instance = REGISTER[data['id']];
    if (instance.paginator) {
        instance.paginator.page = $(this).val() || $(this).data()['page'] || 1;
    };
    jqxhr = handlerCollectionGet(instance);
    return jqxhr
}

/* Обработчик события удаления значения в поле выбора */
function eventFieldClear() {
    if (DEBUG) {console.log('function:'+'eventFieldClear')};
    $this = $(this);
    $this.attr('disabled', 'disabled');
    $this.siblings('button[name]').val(null).html('&nbsp;').change();
    return true
}

/* Обработчик события запуска выбора */
function handlerFieldSelect($field) {
    if (DEBUG) {console.log('function:'+'handlerFieldSelect')};
    FIELD = $field;
    $modal = $('#modal');
    data = $field.data();
    object = REGISTER[data.id];
    model =  REGISTER[validatorID(data.model)];
    selector = new classSelector(model);
    modal = {};
    modal.header = 'Выберите требуемый объект'
    modal.body = handlerLayoutRender(selector, true)
    html = TEMPLATES.modal({modal:modal})
    $modal.html(html).modal('show');
    handlerCollectionGet(selector)
}


/* Обработчик события выбора объекта */
function eventObjectSelect() {
    if (DEBUG) {console.log('function:'+'eventObjectSelect')};
    $this = $(this);
    data = $this.data();
    FIELD.val(data.pk).text(data.unicode).change()
        .siblings('button[disabled]').removeAttr('disabled');
    $('#modal').modal('hide');
    return true
}

/* Обработчик события выбора значения */
function eventFieldSelect() {
    if (DEBUG) {console.log('function:'+'eventFieldSelect')};
    $this = $(this);
    $field = $this.siblings('button[name]');
    handlerFieldSelect($field);
    return true
}

/* Обработчик события выбора строки в таблице */
function eventRowClick() {
    if (DEBUG) {console.log('function:'+'eventRowClick')};
    $this = $(this);
    $this.addClass('info').siblings('tr').removeClass('info');
    return true
}

////////////////////////////////////////////////////////////////////////
//                              ВКЛАДКИ                               //
////////////////////////////////////////////////////////////////////////

function handlerMenuAppLoad() {
    if (DEBUG) {console.log('function:'+'handlerMenuAppLoad')};
    sync = true;
    args = { method: "get_apps" }
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
    return jqxhr
};

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
        }
        // Устанавливаем одиночный биндинг на загрузку контента при щелчке на вкладке
        //~ console.log(tab_id)
        a = $('#tab_'+data.id+' a').one('click', eventLayoutLoad);
        //~ console.log(a)
    }
    return true;
}

/* Обработчик события открытия вкладки */
function eventTabOpen() {
    if (DEBUG) {console.log('function:'+'eventTabOpen')};
    data = $(this).data();
    data = REGISTER[data.id] || data;
    handlerTabOpen(data)
    return true;
}

/* Закрывает вкладку, удаляя её с рабочей области и из настроек */
function handlerTabClose(data) {
    if (DEBUG) {console.log('function:'+'handlerTabClose')};
    $('#tab_'+data.id).remove();
    $('#layout_'+data.id).remove();
    instance = REGISTER[data.id];
    if (instance) {
        handlerObjectRowUnmuted(instance);
        if (instance instanceof classObject) {
            delete REGISTER[data.id]
        }
    };
    // Удаляем из хранилища информацию об открытой вкладке
    num = $.inArray(data.id, SETTINGS.local.tabs);
    if (num > -1) {
        delete SETTINGS.local.tabs[num];
        SETTINGS.cleanTabs().save_local();
    };
}

/* Обработчик события закрытия вкладки */
function eventTabClose() {
    if (DEBUG) {console.log('function:'+'eventTabClose')};
    data = $(this).data();
    data = REGISTER[data.id] || data;
    handlerTabClose(data)
    return true;
}

/* Загружает необходимый макет модели или объекта */
function handlerLayoutLoad(instance) {
    if (DEBUG) {console.log('function:'+'handlerLayoutLoad')};
    html = handlerLayoutRender(instance);
    // Загрузка коллекции
    if ((instance instanceof classModel) || (instance instanceof classCompose)) {
        jqxhr = handlerCollectionGet(instance);
    }
}

/* Обработчик события загрузки макета */
function eventLayoutLoad() {
    if (DEBUG) {console.log('function:'+'eventLayoutLoad')};
    data = $(this).data();
    instance = REGISTER[data.id];
    handlerLayoutLoad(instance)
    // Удаление атрибута загрузки
    $(this).removeAttr("data-loading");
    return true;
}

/* Восстанавливает вкладки, открытые до обновления страницы */
function restoreSession() {
    if (DEBUG) {console.log('function:'+'restoreSession')};
    $.each(SETTINGS.local.tabs, function(i, item) {
        // только приложения в меню
        $('#menu-app li[class!=disabled] a[data-id='+item+']').click();
    });
}

////////////////////////////////////////////////////////////////////////
//                              ПРОЧЕЕ                                //
////////////////////////////////////////////////////////////////////////

function toggleCheckboxes() {
    $table = $(this).parents('table');
    $inputs = $table.find("tbody td:nth-child(1) input[type=checkbox]")
    checked = this.checked
    $.each($inputs, function(i, item) { item.checked = checked });
} 

////////////////////////////////////////////////////////////////////////
//                            ИСПОЛНЕНИЕ                              //
////////////////////////////////////////////////////////////////////////

/* Выполнение чего-либо после загрузки страницы */
$(document).ready(function($) {
    if (DEBUG) {console.log('function:'+'$(document).ready')};
    // Инициализация шаблонов Underscore
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

    // Загрузка меню
    $('#menu-app').hide();
    $('#menu-func').hide();
    handlerMenuAppLoad()

    /* Инициализируем настройки */
    window.SETTINGS = new classSettings();

    /* Инициализируем модальное окно */
    //~ $('#modal').modal();

    // Инициализация для Bootstrap
    $("alert").alert();
    $(".dropdown-toggle").dropdown();

    /* Подсветка ссылок навигатора согласно текущего положения
     * TODO: выяснить необходимость?
    var path = window.location.pathname;
    if (path != '/') { $('div.navbar a[href^="'+path+'"]').parents('li').addClass('active');}
    else { $('div.navbar a[href="/"]').parents('li').addClass('active');}
    */

    // Если настройки готовы, то запускаем все процессы
    if (SETTINGS.init().ready) {
        $('#search').focus();
        $('body').on('click',  'tr[data-pk]', eventRowClick);
        // Биндинги на открытие-закрытие вкладок и их контента
        $('#menu-app li[class!=disabled]').on('click',  'a', eventTabOpen);
        $('#main-tab').on('click', 'button.close[data-id]',  eventTabClose)

        restoreSession();

        // Биндинг на фильтрацию, паджинацию и количество в коллекциях
        $('body').on('keyup',  '[data-action=collection_filter]', eventCollectionFilter);
        $('body').on('change', '[data-action=collection_filter]', eventCollectionFilter);
        $('body').on('click',  '[data-action=collection_count]',  eventCollectionCount);
        $('body').on('change', '[data-action=collection_page]',   eventCollectionPage);
        $('body').on('click',  '[data-action=collection_page]',   eventCollectionPage);

        // Биндинги на кнопки и ссылки
        $('body').on('click', '[data-action=object_open]',   eventObjectOpen);
        $('body').on('click', '[data-action=object_copy]',   eventObjectCopy);
        $('body').on('click', '[data-action=object_add]',                 eventObjectAdd);
        $('body').on('click', '[data-action=object_add_m2m]', {m2m:true}, eventObjectAdd);
        $('body').on('click', '[data-action=object_delete]',                 eventObjectDelete);
        $('body').on('click', '[data-action=object_delete_m2m]', {m2m:true}, eventObjectDelete);
        $('body').on('keyup', '[data-action=object_change]', eventObjectChange);
        $('body').on('change','[data-action=object_change]', eventObjectChange);
        $('body').on('click', '[data-action=object_reset]',  eventObjectReset);
        $('body').on('click', '[data-action=object_save]',   eventObjectSave);
        $('body').on('click', '[data-action=object_select]', eventObjectSelect);

        // Биндинги на кнопки выбора значения
        $('body').on('click', '[data-action=field_clear]',   eventFieldClear);
        $('body').on('click', '[data-action=field_select]',  eventFieldSelect);

        // Биндинг на чекбоксы
        $('body').on('click', '[data-toggle=checkboxes]',   toggleCheckboxes);
        
    } else {
        console.log("ОШИБКА! Загрузка настроек не удалась.");
    }
});
