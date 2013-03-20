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

var TEMPLATES = {};

/* Глобальный объект объектов DB
 * Пример использования:
========================================================================
OBJECTS.append(object1) // добавление в словарь
OBJECTS.append([ object1, object2, ... ]) // добавление в словарь

OBJECTS.update(keyobject1, htmlwidget) // изменение объекта на странице

OBJECTS.remove([ keyobject1, keyobject2, ... ]) // пометка на удаление для коммита
OBJECTS.commit() // отправка на сервер всех изменений по всем моделям
OBJECTS.commit(keymodel) // отправка на сервер списка всех изменённых объектов одной модели
OBJECTS.commit([ keyobject1, keyobject2, ... ]) // отправка на сервер списка объектов
OBJECTS.reload([ keyobject1, keyobject2, ... ]) // перезакгрузка из базы
========================================================================
* */
function Objects() {
    if (DEBUG) {console.log('function:'+'Objects')};
    /* Установка ссылки на свой объект для вложенных функций */
    self = this;
    /* Хранилища объектов */
    _objects = {};

    /* Добавление или замена существующих */
    _append = function(objects) {
        // преобразовываем единственный в список
        if ($.type(objects) != 'array') { objects = [objects] };
        keys = []
        $.each(objects, function(index, item) {
            // Обычный объект модели с полями и ключом
            if (item.pk && item.model && item.fields) {
                key = item.model+'.'+item.pk;
                _objects[key] = item;
                keys.push(key);
            }
            // Объект без ключа, т.е. новый
            else if (item.temppk && item.model && item.fields) {
                key = item.model+'.'+item.temppk;
                _objects[key] = item;
                keys.push(key);
            }
            // Объект не подходит ни подо что
            else {
                console.log('Ошибка добавления объекта:');
                console.log(item);
            };
        });
        return keys;
    };
    this.append = _append

    /* Фиксация изменений, произведённых на странице */
    _update = function(key, widget) {
        name      = $(widget).attr('name');
        value     = $(widget).attr('value');
        datavalue = $.data(widget, 'value') || $(widget).attr('data-value');

        if ($.type(name)      === "undefined") {return false;}
        if ($.type(value)     === "undefined") {return false;}
        if ($.type(datavalue) === "undefined") {return false;}

        field = _objects[key]['fields'][name];
        if ($.type(field) === "array") { field = [datavalue, value] }
        else { field = datavalue };
        return true;
    };
    this.update = _update

    /* Пометка на удаление для коммита или удаление нового,
     * ещё не созданного на сервере.
     */
    _remove = function(keys) {
        notexists = []
        $.each(keys, function(index, key) {
            if (_objects[key]) {
                if (_objects[key]['new']) {
                    delete _objects[key];
                } else { _objects[key]['remove'] = true; };
            } else { notexists.push(key) };
        });
        return notexists;
    };
    this.append = _append

    /* Отправка на сервер в синхронном режиме.
     * Аргументом может выступать:
     * - название модели, например "auth.user" (сохранит все измененные объекты модели);
     * - список ключей объектов (сохранит выбранные объекты с изменениями)
     * Если аргумент отсутствует - сохранит все изменённые объекты.
     */
    _commit = function(keys) {
        objects = []
        sync = true;
        args = { method: "commit", objects: objects };

        // Проверка на изменения
        _valid = function(item) {
            if (item.change || item.remove || item.new) { return true; };
            return false;
        };

        // Выборка всех
        if ($.type(keys) === "undefined") {
            $.each(_objects, function(key, item) {
                if (_valid(item)) { objects.push(item) }
            });
        }
        // Выборка по модели
        else if ($.type(keys) === "string") {
            $.each(_objects, function(key, item) {
                if ((item.model == keys) && (_valid(item))) {
                    objects.push(item)
                }
            });
        }
        // Выборка указанных списком
        else if ($.type(keys) === "array") {
            $.each(keys, function(index, key) {
                item = _objects[key]
                if (_valid(item)) { objects.push(item) }
            });
        };

        // Callback ответа сервера
        cb = function(json, status, xhr) {
            // Сервер ответил False
            if (!json.data) { showAlert(json.message) }
            // Нормальный ответ
            else {
                _last_commit = new Date();
                $.each(keys, function(index, item) {
                    if (_objects[item]['remove'] || _objects[item]['new']) {
                        delete _objects[item]
                    }
                });
            }
        }
        jqxhr = new jsonAPI(args, cb, 'OBJECTS.commit() call jsonAPI()', sync)
        return jqxhr;
    };
    this.commit = _commit

    /* Загрузка с сервера актуальных данных */
    // TODO: реализовать
    _reload = function(keys) {};
    this.reload = _reload
}

/* Формирует HTML на вкладке объекта */
function createObjectContent(data) {
    if (DEBUG) {console.log('function:'+'createObjectContent')};
    html = TEMPLATES.tabContentObject(data);
    $('#tab-content_'+data.id).html(html);
    OBJECTS.append(data)
    //~ TODO: сделать загрузку композиций
};

/* Обрабатывает изменения полей объекта */
function changeFieldObject() {
    if (DEBUG) {console.log('function:'+'changeFieldObject')};
    console.log('changeFieldObject()');
}

/* Восстанавливает объект */
function resetObject() {
    if (DEBUG) {console.log('function:'+'resetObject')};
}

/* Сохраняет объект в DB */
function saveObject(self) {
    if (DEBUG) {console.log('function:'+'saveObject')};
    $self = $(this); // button
    //~ model = $self.attr('data-model');
    //~ object = $self.attr('data-object');
    //~ html_id = $self.attr('data-html-id');
    //~ tab = $('#tab-content-'+html_id+'_object')
    //~ form = $('#form-'+html_id+'_object');
    //~ if (object) {
        //~ args = { 
            //~ method:'object_action', model:model, key:'upd',
            //~ pk:object, ARRAY_FORM_OBJECT_KEY: form.serializeArray(),
        //~ }
        //~ callback = function(json, status, xhr) {
            //~ var data = json.data;
            //~ createObjectContent(data);
        //~ };
        //~ jqxhr = new jsonAPI(args, callback, 'saveObject() "if (object)" call jsonAPI()');
    //~ }
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

/* Сохраняет вложенные объекты в DB */
function saveCompose() {
    if (DEBUG) {console.log('function:'+'saveCompose')};
    $self = $(this); // button
    //~ model = $self.attr('data-model');
    //~ object = $self.attr('data-object');
    //~ html_id = $self.attr('data-html-id');
    //~ tab = $('#tab-content-'+html_id+'_object')
    //~ form = $('#form-'+html_id+'**************COMPOSE*********');
    //~ if (object) {
        //~ args = { 
            //~ method:'object_action', model:model, key:'set',
            //~ pk:object, arrayObjectForm: form.serializeArray(),
        //~ }
        //~ callback = function(json, status, xhr) {
            //~ var data = json.data;
        //~ };
        //~ jqxhr = new jsonAPI(args, callback, 'saveObject() "if (object)" call jsonAPI()');
    //~ }
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
 *  >> "gen1363655293735"
 *  >> id = generatorID(null, "object")
 *  >> "gen1363655293736_object"
 *  >> id = generatorID("object")
 *  >> "object_gen1363655293737"
 *  >> id = generatorID("model", "object")
 *  >> "model_gen1363655293738_object"
 */
function generatorID(prefix, postfix) {
    if (DEBUG) {console.log('function:'+'generatorID')};
    var result = 'gen';
    if (prefix) { result += prefix + '_' };
    result += $.now();
    if (postfix) { result += '_' + postfix };
    return validatorID(result);
}

/* Приводит идентификаторы в позволительный jQuery вид.
 * В данном приложении он заменяет точки на "-"
 */
function validatorID(string) {
    if (DEBUG) {console.log('function:'+'validatorID')};
    return string.replace(/[\.,\:,\/, ,\(,\),=,?]/g, "-");
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
//                            DATATABLES                              //
////////////////////////////////////////////////////////////////////////

/* Инициализация DataTables */
function initDataTables(data) {
    if (DEBUG) {console.log('function:'+'initDataTables')};
    table = function() { return $('table[data-model="'+data.model+'"]');}
    if (table().length < 1) {
        html = TEMPLATES.datatables(data);
        $('#tab-content_'+data.id).html(html);
    };
    /* Init DataTables */
    var oTable = table().dataTable({
        "oLanguage": { "sUrl": "static/js/dataTables/1.9.4/"+data.oLanguage+".txt" },
        //~ "sScrollY": '400px',
        "bProcessing": data.bProcessing,
        "bServerSide": data.bServerSide,
        "sAjaxSource": data.sAjaxSource,
        "sServerMethod": data.sServerMethod,
        "fnServerParams": function ( aoData ) {
            $.each(data.fnServerParams, function(i,val) {
                aoData.push( { "name": val[0], "value": val[1] } );
            });
        },
        "fnRowCallback": function( nRow, aData, iDisplayIndex ) {
            $(nRow).bind("click", function() {
                $(oTable).find('tbody tr.info').removeClass('info');
                if (DEBUG) { console.log('addClass("info")') };
                $(nRow).addClass('info');
            })
        },
        "fnCreatedRow": function( nRow, aData, iDataIndex ) {
            html = TEMPLATES.datatables_pk({ data: data, aData: aData });
            $('td:eq(0)', nRow).html(html).find('a').click(addTab);
        },
        "aoColumnDefs": data.aoColumnDefs,
        "sPaginationType": "bootstrap",
        "sDom": data.sDom || 'lfrtip',
        "bLengthChange": data.bLengthChange || true,
        "bStateSave": data.bStateSave || true,
        "fnServerData": function( sUrl, aoData, fnCallback, oSettings ) {
            oSettings.jqXHR =  $.ajax( {
                "url": sUrl,
                "data": aoData,
                "method": "post",
                "success": fnCallback,
                "dataType": "json",
                "cache": false
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
        }
    });
    /* Apply after */
    //~ console.log( $($(oTable).attr('id')+'_wrapper'))
    //~ filter = $(oTable).parent().parent().find('.dataTables_filter');
    //~ filter.find('label').text('text');
    //~ console.log(filter.html())
    return false;
}

/* Обработчик двойного клика по строке в таблице модели */
function dblClickRow(oTable, nRow) {
    if (DEBUG) {console.log('function:'+'dblClickRow')};
    console.log(oTable);
    console.log(nRow);
    //~ $('div.toolbar').html('<button class="btn btn-primary btn-mini">Btn</button>');
}

/* Table showing and hiding columns */
function fnShowHide( model, iCol ) {
    if (DEBUG) {console.log('function:'+'fnShowHide')};
    table = $('table[data-model="'+model+'"]');
    /* Get the DataTables object again - this is not a recreation, just a get of the object */
    var oTable = table.dataTable();
    var bVis = oTable.fnSettings().aoColumns[iCol].bVisible;
    oTable.fnSetColumnVis( iCol, bVis ? false : true );
    return false;
}


////////////////////////////////////////////////////////////////////////
//                              ВКЛАДКИ                               //
////////////////////////////////////////////////////////////////////////

/* Добавляет вкладки на рабочую область */
function addTab() {
    if (DEBUG) {console.log('function:'+'addTab')};
    data          = $(this).data();
    data['title'] = $(this).attr('title') || $(this).attr('data-title') || '';
    data['text']  = $(this).attr('data-text') || $(this).text() || data.title;
    data['id'] = data.pk ? validatorID(data.model+'_'+data.pk) : validatorID(data.model);
    if (!data.pk) {data.pk = null}; // для передачи в шаблон
    if (data.pk) { $(this).addClass('muted'); }

    tab = $('#main-tab #tab_'+ data.id);
    if (tab.length > 0) {
        // Отображаем вкладку
        tab.find('a').tab('show');
    } else {
        // Контент вкладки
        html = TEMPLATES.tabContentDefault(data);
        $('#main-tab-content').append(html);
        // Сама вкладка
        html = TEMPLATES.tab(data);
        $('#main-tab').append(html);
        // Отображаем вкладку c небольшой задержкой
        delay(function() {
            a = $('#main-tab a:last').tab('show');
            contentLoader(a[0]);
        }, 1);
        // Добавляем вкладку в хранилище, если её там нет
        // (т.к. эту же функцию использует восстановление сессии). 
        if ($.inArray(data.id, SETTINGS.local.tabs) < 0) {
            SETTINGS.local.tabs.push(data.id);
            SETTINGS.save_local();
        }
        // Устанавливаем одиночный биндинг на загрузку контента при щелчке на вкладке
        //~ console.log(tab_id)
        a = $('#tab_'+data.id+' a').one('click', function() { contentLoader(this) });
        //~ console.log(a)
    }
    return true;
}

/* Удаляет вкладки с рабочей области и из локальной памяти */
function removeTab() {
    if (DEBUG) {console.log('function:'+'removeTab')};
    id = validatorID($(this).attr('data-id'));
    $('#tab_'+id).remove();
    $('#tab-content_'+id).remove();
    // Удаляем из хранилища информацию об открытой вкладке
    num = $.inArray(id, SETTINGS.local.tabs);
    if (num > -1) {
        delete SETTINGS.local.tabs[num];
        SETTINGS.cleanTabs().save_local();
    };
}

/* Загружает во вкладку необходимый контент */
function contentLoader(obj) {
    if (DEBUG) {console.log('function:'+'contentLoader')};
    // Загрузка контента во вкладку
    $obj = $(obj);
    model  = $obj.attr('data-model');
    pk = $obj.attr('data-pk');
    // Загрузка объекта модели
    if (pk) {
        args = { method:'object_action', model:model, key:'get', pk:pk }
        callback = function(json, status, xhr) {
            createObjectContent(json.data);
        };
        jqxhr = new jsonAPI(args, callback, 'contentLoader(obj) "if (pk)" call jsonAPI()');
    }
    // Загрузка модели приложения (Datatables.net)
    else if (model) {
        args = { method:'datatables_info', model: model, info: true }
        callback = function(json, status, xhr) {
            initDataTables(json.data);
        }
        jqxhr = new jsonAPI(args, callback, 'contentLoader(obj) "if (model)" call jsonAPI()');
    }
    // Удаление привязки клика на вкладке
    $obj.unbind('click');
    return jqxhr
}

/* Восстанавливает вкладки, открытые до обновления страницы */
function restoreSession() {
    if (DEBUG) {console.log('function:'+'restoreSession')};
    $.each(SETTINGS.local.tabs, function(i, item) {
        $('[data-id='+item+']').click(); // только приложения в меню
    });
}


////////////////////////////////////////////////////////////////////////
//                            ИСПОЛНЕНИЕ                              //
////////////////////////////////////////////////////////////////////////

/* Выполнение чего-либо после загрузки страницы */
$(document).ready(function($) {
    if (DEBUG) {console.log('function:'+'$(document).ready')};
    /* сначала инициализируем объекты, затем настройки, иначе не работает
     * TODO: Найти объяснение.
     */
    window.OBJECTS = new Objects();
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


    // Инициализация шаблонов Underscore
    TEMPLATES.alert = _.template($('#underscore-alert').html());
    TEMPLATES.tabContentObject = _.template($('#underscore-tab-content-object').html());
    TEMPLATES.tabContentDefault = _.template($('#underscore-tab-content-default').html());
    TEMPLATES.tab = _.template($('#underscore-tab').html());
    TEMPLATES.datatables = _.template($('#underscore-datatables').html());
    TEMPLATES.datatables_pk = _.template($('#underscore-datatables-pk').html());

    // Если настройки готовы, то запускаем все процессы
    if (SETTINGS.init().ready) {
        $('#search').focus();
        // Биндинги на открытие-закрытие вкладок и их контента
        $('#menu-app li[class!=disabled] a[data-model]').click(addTab);
        $('#main-tab').on('click', 'button.close[data-id]', removeTab)

        restoreSession();

        // Биндинги на кнопки
        $('body').on('click', 'button[data-action=reset-object]:enabled', resetObject);
        $('body').on('click', 'button[data-action=save-object]:enabled',  saveObject);
        $('body').on('submit', 'form[id^=form-object]', submitFormObject);

        // Биндинги на поля объектов
        $('body').on('change', 'select[data-type=object_field]:enabled', changeFieldObject);
        $('body').on('change', 'input[data-type=object_field]:enabled', changeFieldObject);
        
    } else {
        console.log("ОШИБКА! Загрузка настроек не удалась.");
    }
});

