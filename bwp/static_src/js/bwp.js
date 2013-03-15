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
//                            НАСТРОЙКИ                               //
////////////////////////////////////////////////////////////////////////

window.SETTINGS = new Settings();
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

////////////////////////////////////////////////////////////////////////
//                               ОБЩИЕ                                //
////////////////////////////////////////////////////////////////////////

/* Единая, переопределяемая задержка для действий или функций */
var delay = (function(){
  var timer = 0;
  return function(callback, ms){
    clearTimeout (timer);
    timer = setTimeout(callback, ms);
  };
})();

/* Общие функции вывода сообщений */
function hideAlert() { $('.alert').alert('close'); }
function showAlert(msg, type, callback) {
    console.log(msg);
    if (!type) { type = 'alert-error' }
    html = Jinja.render($('#jinja-alert').html(), { msg: msg, type: type });
    $('#alert-place').html(html);
    $(window).scrollTop(0);
    $('.alert').alert();
    if (callback) { delay(callback, 5000);
    } else { delay(hideAlert, 5000); }
    return false;
}

/* Общая функция для работы с django-quickapi */
function jsonAPI(args, callback, to_console, sync) {
    if (DEBUG) {console.log($.toJSON(args))};
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
            // Иначе заменяем содержимое страницы ответом
            // TODO: нужно придумать что-то получше...
            $("html").html(xhr.responseText);
        };
    })
    // Обработка полученных данных
    .done(function(json, status, xhr) {
        if (to_console) { if (DEBUG) {console.log(to_console)}; };
        if ((json.status >=300) && (json.status <400) && (json.data.Location)) {
            // При переадресации нужно отобразить сообщение,
            // а затем выполнить переход по ссылке, добавив параметр для
            // возврата на текущую страницу
            showAlert(json.message, 'alert-error', function() {
                window.location.href = json.data.Location
                .replace(/\?.*$/, "?next=" + window.location.pathname);
            });
        } else if (json.status >=400) {
            // При ошибках извещаем пользователя
            showAlert(json.message, 'alert-error');
        } else {
            // При нормальном возврате
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
    table = $('table[data-model="'+data.model+'"]');
    template = $('#jinja-datatables-column-pk').html();
    /* Init DataTables */
    var oTable = table.dataTable({
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
            $(nRow)
            .bind("click", function() {
                $(oTable).find('tbody tr.info').removeClass('info');
                if (DEBUG) { console.log('click') };
                $(nRow).addClass('info');
            })
            //~ .bind("dblclick", function() {
                //~ dblClickRow(oTable, nRow)
            //~ });
        },
        "fnCreatedRow": function( nRow, aData, iDataIndex ) {
            html = Jinja.render(template, { data: data, aData: aData });
            $('td:eq(0)', nRow).html(html).find('a').click(addTab);
        },
        "aoColumnDefs": data.aoColumnDefs,
        "sPaginationType": "bootstrap",
        "sDom": data.sDom || 'lfrtip',
        "bLengthChange": data.bLengthChange || true,
        "bStateSave": data.bStateSave || true,
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
    console.log(oTable);
    console.log(nRow);
    //~ $('div.toolbar').html('<button class="btn btn-primary btn-mini">Btn</button>');
}

/* Table showing and hiding columns */
function fnShowHide( model, iCol ) {
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
    data   = $(this).data();
    tab_id = data.tabId;
    if (data.object) { $(this).addClass('muted'); }
    
    tab = $('#main-tab #tab-'+ tab_id);
    
    if (tab.length > 0) {
        // Отображаем вкладку
        tab.find('a').tab('show');
    } else {
        // Контент вкладки
        html = Jinja.render($('#jinja-tab-default-content').html(), { data: data });
        $('#main-tab-content').append(html);
        // Сама вкладка
        html = Jinja.render($('#jinja-tab').html(), { data: data });
        $('#main-tab').append(html);
        // Отображаем вкладку c небольшой задержкой
        delay(function() {
            a = $('#main-tab a:last').tab('show');
            contentLoader(a[0]);
        }, 200);
        // Переустанавливаем биндинги на закрытие вкладок и их контента
        $('#main-tab li button.close').unbind('click').click(function() {
            close_tab_id = $(this).attr('data-close');
            $('#tab-'+close_tab_id).remove();
            $('#tab-content-'+close_tab_id).remove();
            // Удаляем из хранилища информацию об открытой вкладке
            num = $.inArray(close_tab_id, SETTINGS.local.tabs);
            if (num > -1) {
                delete SETTINGS.local.tabs[num];
                SETTINGS.cleanTabs().save_local();
            };
        });
        // Добавляем вкладку в хранилище, если её там нет
        // (т.к. эту же функцию использует восстановление сессии). 
        if ($.inArray(tab_id, SETTINGS.local.tabs) < 0) {
            SETTINGS.local.tabs.push(tab_id);
            SETTINGS.save_local();
        }
        // Устанавливаем одиночный биндинг на загрузку контента при щелчке на вкладке
        //~ console.log(tab_id)
        a = $('#tab-'+tab_id+' a').one('click', function() {contentLoader(this)});
        //~ console.log(a)
    }
    return true;
}

/* Загружает во вкладку необходимый контент */
function contentLoader(obj) {
    // Загрузка контента во вкладку
    $obj = $(obj);
    model  = $obj.attr('data-model');
    func   = $obj.attr('data-func');
    object = $obj.attr('data-object');
    if (object) {
        args = { method:'object_action', model:model, key:'get', pk:object }
        callback = function(json, status, xhr) {
            var data = json.data;
            createObjectContent(data);
        };
        jqxhr = new jsonAPI(args, callback, 'contentLoader(obj) "if (object)" call jsonAPI()');
    } else if (model) {
        jqxhr = new $.getJSON(BWP_DATATABLES_URL, { model: model, info: true },
            function(data, status) {
                $('#tab-content-'+data.html_id).html(data.html);
                initDataTables(data);
            }
        );
    } else if (func) {
        if (DEBUG) { console.log('Type is func') };
    }
    // Удаление привязки клика на вкладке
    $obj.unbind('click');
    return jqxhr
}

/* Восстанавливает вкладки, открытые до обновления страницы */
function restoreSession() {
    $.each(SETTINGS.local.tabs, function(i, item) {
        $('[data-tab-id='+item+']').click();
    });
}

////////////////////////////////////////////////////////////////////////
//                              ОБЪЕКТЫ                               //
////////////////////////////////////////////////////////////////////////

/* Формирует HTML на вкладке объекта */
function createObjectContent(data) {
    html = Jinja.render($('#jinja-object-tab-content').html(), { data: data });
    $('#tab-content-'+data.html_id).html(html);
    //~ TODO: сделать загрузку композиций
};

/* Восстанавливает объект */
function resetObject() {
    console.log('resetObject()');
    $self = $(this); // button
    model = $self.attr('data-model');
    object = $self.attr('data-object');
    html_id = $self.attr('data-html-id');
    tab = $('#tab-content-'+html_id+'_object')
    form = $('#form-'+html_id+'_object');
    //~ form.resetForm();
}

/* Сохраняет объект в DB */
function saveObject(self) {
    $self = $(this); // button
    model = $self.attr('data-model');
    object = $self.attr('data-object');
    html_id = $self.attr('data-html-id');
    tab = $('#tab-content-'+html_id+'_object')
    form = $('#form-'+html_id+'_object');
    if (object) {
        args = { 
            method:'object_action', model:model, key:'upd',
            pk:object, ARRAY_FORM_OBJECT_KEY: form.serializeArray(),
        }
        callback = function(json, status, xhr) {
            var data = json.data;
            createObjectContent(data);
        };
        jqxhr = new jsonAPI(args, callback, 'saveObject() "if (object)" call jsonAPI()');
    }
}

/* Сохраняет объект в DB без нажатия на кнопку */
function submitFormObject() {
    $(this).find('button[data-action=save]:enabled').click();
}

/* Восстанавливает вложенные объекты */
function resetCompose() {
    console.log('resetCompose()');
}

/* Сохраняет вложенные объекты в DB */
function saveCompose() {
    $self = $(this); // button
    model = $self.attr('data-model');
    object = $self.attr('data-object');
    html_id = $self.attr('data-html-id');
    tab = $('#tab-content-'+html_id+'_object')
    form = $('#form-'+html_id+'**************COMPOSE*********');
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
//                            ИСПОЛНЕНИЕ                              //
////////////////////////////////////////////////////////////////////////

/* Execute something after load page */
$(document).ready(function($) {
    $("alert").alert();
    if (SETTINGS.init().ready) {
        $(".dropdown-toggle").dropdown();
        var path = window.location.pathname;
        if (path != '/') { $('div.navbar a[href^="'+path+'"]').parents('li').addClass('active');}
        else { $('div.navbar a[href="/"]').parents('li').addClass('active');}
        $('#search').focus();
        $('#menu-app li[class!=disabled] a[data-tab-id]').click(addTab);

        restoreSession();

        // Биндинги на кнопки
        $('body').on('click', 'button[data-action=reset-object]:enabled', resetObject);
        $('body').on('click', 'button[data-action=save-object]:enabled',  saveObject);
        $('body').on('submit', 'form[id$=_object]', submitFormObject);
        
    };
});

