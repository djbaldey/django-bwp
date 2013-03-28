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
//                              ОБЪЕКТЫ                               //
////////////////////////////////////////////////////////////////////////
var NEWITEMKEY = 'newItem';

// Глобальные хранилища-регистраторы
window.TEMPLATES = {}; // Шаблоны
window.REGISTER  = {}; // Регистр приложений, моделей, композиций и объектов

/* класс: Приложение BWP */
function App(data) {
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
        _models.push(new Model(app, item));
    });
    // Register
    REGISTER[this.id] = this;
};

function renderCollection(object) {
    if (DEBUG) {console.log('function:'+'renderCollection')};
    if (object instanceof Item) {  
        return '';
    }
    html = TEMPLATES.collection({data:object})
    $('#collection_'+object.id).html(html)
    return html
}

function renderLayout(object) {
    if (DEBUG) {console.log('function:'+'renderLayout')};
    if (object instanceof Model) {  
        template = TEMPLATES.layoutModel
    }
    else if (object instanceof Compose) {  
        template = TEMPLATES.layoutCompose
    }
    else if (object instanceof Item) {  
        template = TEMPLATES.layoutItem
    }
    html = template({data:object})
    $('#layout_'+object.id).html(html)
    return html
}

/* класс: Модель BWP */
function Model(app, data) {
    this.app   = app;
    this.perms = data.perms;
    this.meta  = data.meta;
    this.name  = data.name;
    this.model = this.name;
    this.id    = validatorID(this.model);
    this.label = data.label;
    this.title = this.app.label +': '+ this.label;
    this.query = null;
    this.paginator = {};
    _composes     = {};
    this.composes = _composes
    _widgets = [];
    this.widgets = _widgets;
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

/* класс: Композиция */
function Compose(item, data) {
    this.item     = item;
    this.editable = Boolean(this.item.pk);
    this.perms    = data.perms;
    this.meta     = data.meta;
    this.name     = this.meta.related_name;
    this.compose  = this.name;
    this.model = this.meta.related_model;
    this.id    = validatorID([this.item.id, this.name]);
    this.label = data.label;
    this.title = this.item.label +': '+ this.label;
    this.query = null;
    this.paginator = null;
    _widgets = [];
    this.widgets = _widgets;
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
function Item(data) {
    this.model = REGISTER[validatorID(data.model)];
    this.pk    = data.pk;
    this.id    = this.pk ? validatorID(data.model+'.'+this.pk) : generatorID(NEWITEMKEY);
    this.__unicode__ = data.__unicode__;
    this.label       = this.__unicode__;
    this.title = this.model.label +': '+ this.label;
    _fields     = data.fields;
    this.fields = _fields;
    _tmpfields     = {};
    this.tmpfields = _tmpfields;
    _composes = [];
    this.composes = _composes;
    this.widgets = this.model.meta.widgets;
    object = this;
    // Init
    if (this.model.composes) {
        $.each(this.model.composes, function(rel_name, item) {
            _composes.push(new Compose(object, item));
        });
    }
    // register
    REGISTER[this.id] = this;
};

function objectOpen() {
    if (DEBUG) {console.log('function:'+'objectOpen')};
    $this = $(this);
    data = $this.data();
    if (!data.model) { return false };
    object = REGISTER[data.id];
    if (object) {
        tabAdd(object);
        return null
    }
    args = {
        "method"  : "get_object",
        "model"   : data.model,
        "pk"      : data.pk || null,
    }
    cb = function(json, status, xhr) {
        object = new Item(json.data);
        $this.data('id', object.id);
        tabAdd(object);
    }
    jqxhr = new jsonAPI(args, cb, 'objectOpen() call jsonAPI()')
    return jqxhr
}

function objectNew() {
    if (DEBUG) {console.log('function:'+'objectNew')};
    $this = $(this);
    data = $this.data();
    object = REGISTER[data.id];
}

function objectCopy() {
    if (DEBUG) {console.log('function:'+'objectCopy')};
    $this = $(this);
    data = $this.data();
    object = REGISTER[data.id];
}

function objectDelete() {
    if (DEBUG) {console.log('function:'+'objectDelete')};
    $this = $(this);
    data = $this.data();
    object = REGISTER[data.id];
}

function objectSave() {
    if (DEBUG) {console.log('function:'+'objectSave')};
    $this = $(this);
    data = $this.data();
    object = REGISTER[data.id];
}

function mutedObjectRow(object) {
    if (DEBUG) {console.log('function:'+'mutedObjectRow')};
    $('tr[data-model="'+object.model.name+'"][data-pk="'+object.pk+'"]')
        .addClass('muted');
}

function unmutedObjectRow(object) {
    if (DEBUG) {console.log('function:'+'unmutedObjectRow')};
    $('tr[data-model="'+object.model.name+'"][data-pk="'+object.pk+'"]')
        .removeClass('muted');
}

/* Функция получает коллекцию с сервера и перерисовывает цель
 * коллекции модели/композиции, для которых она вызывалась
 */
function getCollection(object) {
    if (DEBUG) {console.log('function:'+'getCollection')};
    args = {
        "method"  : "get_collection",
        "model"   : object.model,
        "compose" : object.compose       || null,
        "order_by": object.meta.ordering || null,
    }
    args[object.meta.search_key] = object.query || null;
    if (object.item) {
        args["pk"] = object.item.pk || 0;
    };
    if (object.paginator) {
        args["page"]    = object.paginator.page     || 1;
        args["per_page"]= object.paginator.per_page || null;
    };
    cb = function(json, status, xhr) {
        object.paginator = json.data;
        html = renderCollection(object);
        //~ console.log(html)
    }
    jqxhr = new jsonAPI(args, cb, 'getCollection() call jsonAPI()')
    return jqxhr
}

function collectionFilter() {
    if (DEBUG) {console.log('function:'+'collectionFilter')};
    search = this;
    data   = $(search).data();
    object = REGISTER[data['id']];
    object.query = $(search).val() || null;

    jqxhr = getCollection(object);
    return jqxhr
}

function collectionCount() {
    if (DEBUG) {console.log('function:'+'collectionCount')};
    data   = $(this).data();
    object = REGISTER[data['id']];
    if (object.paginator) {
        object.paginator.page = 1;
        object.paginator.per_page = $(this).val() || $(this)
            .data()['count'] || object.meta.list_per_page;
        $('[data-placeholder=collection_count][data-id='+object.id+']')
            .text(object.paginator.per_page)
    };
    jqxhr = getCollection(object);
    return jqxhr
}

function collectionPage() {
    if (DEBUG) {console.log('function:'+'collectionPage')};
    data   = $(this).data();
    object = REGISTER[data['id']];
    if (object.paginator) {
        object.paginator.page = $(this).val() || $(this).data()['page'] || 1;
    };

    jqxhr = getCollection(object);
    return jqxhr
}

/* Обрабатывает изменения полей объекта */
function changeFieldObject() {
    if (DEBUG) {console.log('function:'+'changeFieldObject')};
    console.log('changeFieldObject()');
}

/* Восстанавливает объект */
function objectReset() {
    if (DEBUG) {console.log('function:'+'objectReset')};
}

/* Сохраняет объект в DB */
function saveObject(self) {
    if (DEBUG) {console.log('function:'+'saveObject')};
    $self = $(this); // button
}

/* Сохраняет объект в DB без нажатия на кнопку */
function submitFormObject() {
    if (DEBUG) {console.log('function:'+'submitFormObject')};
    $(this).find('button[data-action=save]:enabled').click();
}

/* Восстанавливает вложенные объекты */
function resetCompose() {
    if (DEBUG) {console.log('function:'+'resetCompose')};
    console.log('resetCompose()');
}

////////////////////////////////////////////////////////////////////////
//                            НАСТРОЙКИ                               //
////////////////////////////////////////////////////////////////////////

/* Глобальный объект настроек
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
function Settings(default_callback) {
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
            if (!json.data) { showAlert(json.message) }
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
function hideAlert() {
    if (DEBUG) {console.log('function:'+'hideAlert')};
    $('.alert').alert('close');
}
function showAlert(msg, type, callback) {
    if (DEBUG) {console.log('function:'+'showAlert')};
    console.log(msg);
    if (!type) { type = 'alert-error' }
    html = TEMPLATES.alert({ msg: msg, type: type });
    $('#alert-place').html(html);
    $(window).scrollTop(0);
    $('.alert').alert();
    if (callback) { delay(callback, 5000);
    } else { delay(hideAlert, 5000); }
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
            showAlert(_(xhr.responseText).truncate(255), 'alert-error');
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
            showAlert(json.message, 'alert-error', function() {
                window.location.href = json.data.Location
                .replace(/\?.*$/, "?next=" + window.location.pathname);
            });
        }
        /* При ошибках извещаем пользователя полученным сообщением */
        else if (json.status >=400) {
            showAlert(json.message, 'alert-error');
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
//                              ВКЛАДКИ                               //
////////////////////////////////////////////////////////////////////////

function loadMenuApp() {
    if (DEBUG) {console.log('function:'+'loadMenuApp')};
    sync = true;
    args = { method: "get_apps" }
    cb = function(json, status, xhr) {
        apps = [];
        $.each(json.data, function(index, item) {
            apps.push(new App(item));
        });
        html = TEMPLATES.menuApp({data:apps});
        $('#menu-app ul[role=menu]').html(html);
        $('#menu-app').show();
    };
    jqxhr = new jsonAPI(args, cb, 'loadMenuApp() call jsonAPI()', sync);
    return jqxhr
};

/* Добавляет вкладки на рабочую область */
function tabAdd(obj) {
    if (DEBUG) {console.log('function:'+'tabAdd')};
    data = $(this).data();
    if (obj instanceof Item) { data = obj };
    object = REGISTER[data.id] || data;
    mutedObjectRow(object);

    tab = $('#main-tab #tab_'+ object.id);
    if (tab.length > 0) {
        // Отображаем вкладку
        tab.find('a').tab('show');
    } else {
        // Контент вкладки
        html = TEMPLATES.layoutDefault({data: object});
        $('#main-tab-content').append(html);
        // Сама вкладка
        html = TEMPLATES.tab({data: object});
        $('#main-tab').append(html);
        // Отображаем вкладку c небольшой задержкой
        delay(function() {
            a = $('#main-tab a:last').tab('show');
            loadLayout(a[0]);
        }, 1);
        // Добавляем вкладку в хранилище, если её там нет
        // (т.к. эту же функцию использует восстановление сессии). 
        if ((object.id.indexOf(NEWITEMKEY) == -1)&&($.inArray(object.id, SETTINGS.local.tabs) < 0)) {
            SETTINGS.local.tabs.push(object.id);
            SETTINGS.save_local();
        }
        // Устанавливаем одиночный биндинг на загрузку контента при щелчке на вкладке
        //~ console.log(tab_id)
        a = $('#tab_'+object.id+' a').one('click', function() { loadLayout(this) });
        //~ console.log(a)
    }
    return true;
}

/* Удаляет вкладки с рабочей области и из локальной памяти */
function tabRemove() {
    if (DEBUG) {console.log('function:'+'tabRemove')};
    id = validatorID($(this).attr('data-id'));
    $('#tab_'+id).remove();
    $('#layout_'+id).remove();
    object = REGISTER[id];
    if (object) { unmutedObjectRow(object) };
    // Удаляем из хранилища информацию об открытой вкладке
    num = $.inArray(id, SETTINGS.local.tabs);
    if (num > -1) {
        delete SETTINGS.local.tabs[num];
        SETTINGS.cleanTabs().save_local();
    };
}

/* Загружает во вкладку необходимый макет модели или объекта */
function loadLayout(obj) {
    if (DEBUG) {console.log('function:'+'loadLayout')};
    $obj = $(obj);
    data = $obj.data();
    object = REGISTER[validatorID(data.id)];
    html = renderLayout(object);
    // Одиночные биндинги на загрузку коллекций объекта
    if (object instanceof Item) {
        $('#layout_'+object.id+' button[data-loading=true]')
        .one('click', function() { loadLayout(this) });
    }
    // Загрузка коллекции
    else if ((object instanceof Model) || (object instanceof Compose)) {
        jqxhr = getCollection(object);
    }
    // Удаление атрибута загрузки
    $obj.removeAttr("data-loading");
    return $obj
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
    TEMPLATES.layoutCompose     = _.template($('#underscore-layout-compose').html());
    TEMPLATES.layoutItem        = _.template($('#underscore-layout-item').html());
    TEMPLATES.layoutDefault     = _.template($('#underscore-layout-default').html());
    TEMPLATES.tab               = _.template($('#underscore-tab').html());

    // Загрузка меню
    $('#menu-app').hide();
    $('#menu-func').hide();
    loadMenuApp()

    /* сначала инициализируем объекты, затем настройки, иначе не работает
     * TODO: Найти объяснение.
     */
    //~ window.OBJECTS = new Objects();
    window.SETTINGS = new Settings();

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
        // Биндинги на открытие-закрытие вкладок и их контента
        $('#menu-app li[class!=disabled] a').click(tabAdd);
        $('#main-tab').on('click', 'button.close[data-id]', tabRemove)

        restoreSession();

        // Биндинги на поля объектов
        $('body').on('change', 'select[data-type=object_field]:enabled', changeFieldObject);
        $('body').on('change', 'input[data-type=object_field]:enabled', changeFieldObject);

        // Биндинг на фильтрацию, паджинацию и количество в коллекциях
        $('body').on('keyup',  '[data-action=collection_filter]:enabled', collectionFilter);
        $('body').on('change', '[data-action=collection_filter]:enabled', collectionFilter);
        $('body').on('change', '[data-action=collection_count]:enabled',  collectionCount);
        $('body').on('click',  '[data-action=collection_count]',          collectionCount);
        $('body').on('change', '[data-action=collection_page]:enabled',   collectionPage);
        $('body').on('click',  '[data-action=collection_page]',           collectionPage);
        
        // Биндинги на кнопки
        $('body').on('click','[data-action=object_open]',   objectOpen);
        $('body').on('click','[data-action=object_new]',    objectNew);
        $('body').on('click','[data-action=object_copy]',   objectCopy);
        $('body').on('click','[data-action=object_delete]', objectDelete);
        $('body').on('click','[data-action=object_reset]',                objectReset);
        $('body').on('click','button[data-action=object_reset]:enabled',  objectReset);
        $('body').on('click','[data-action=object_save]',               objectSave);
        $('body').on('click','button[data-action=object_save]:enabled', objectSave);
        
    } else {
        console.log("ОШИБКА! Загрузка настроек не удалась.");
    }
});
