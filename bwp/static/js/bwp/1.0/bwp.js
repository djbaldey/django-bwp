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

/* GLOBAL VARS */
_SETTINGS = { tabs: [], } // default
var SETTINGS = {
    values: null,
    init: function() {
        if (typeof localStorage == 'undefined' || typeof JSON == 'undefined')
            { return false; }
        this.values = $.evalJSON(localStorage.getItem('BWP_SETTINGS')) || _SETTINGS;
        return this;
    },
    // Reading data
    read: function() {
        if (this.values == null) { return this.init().values; }
        return this.values;
    },
    // To localStorage
    save: function() {
        string = $.toJSON(this.read())
        localStorage.setItem('BWP_SETTINGS', string)
        return string;
    },
    // Очистка от null в списке вкладок
    cleanTabs: function() {
        _tabs = []
        $.each(this.values.tabs, function(i, item) {
            if (item) { _tabs.push(item); }
        });
        this.values.tabs = _tabs;
        return this;
    }
}

/* One delay for all functions */
var delay = (function(){
  var timer = 0;
  return function(callback, ms){
    clearTimeout (timer);
    timer = setTimeout(callback, ms);
  };
})();

/* Глобальные функции вывода сообщений */
function hideAlert() { $('.alert').alert('close'); }
function showAlert(msg, type, callback) {
    if (!type) { type = 'alert-error' }
    alert = '<div class="alert '+type+' fade in">\
    <button type="button" class="close" data-dismiss="alert">×</button>'
    +'<span class="alert-text">'+msg+'</span></div>'
    $('#alert-place').html(alert);
    $(window).scrollTop(0);
    $('.alert').alert();
    if (callback) { delay(callback, 3000);
    } else { delay(hideAlert, 3000); }
    return false;
}

/* Глобальная функция для работы с django-quickapi */
function jsonAPI(args, callback, to_console) {
    if (!args) { args = { method: "get_settings" } };
    if (!callback) { callback = function(json, status, xhr) {} };
    $.ajax({
        type: "POST",
        url: '/api/',
        data: 'jsonData=' + JSON.stringify(args),
        dataType: 'json',
        success: function(json, status, xhr) {
            if (to_console) { testLog(to_console) };
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
                // При нормальном возврате просто пишем в консоль
                // пришедшее сообщение
                testLog(json.message);
                return callback(json, status, xhr);
            };
        },
        error: function(xhr, status, err) {
            // Если есть переадресация, то выполняем её
            if (xhr.getResponseHeader('Location')) {
                window.location = xhr.getResponseHeader('Location')
                .replace(/\?.*$/, "?next=" + window.location.pathname);
                testLog("1:" + xhr.getResponseHeader('Location'));
            } else {
                // Иначе заменяем содержимое страницы ответом
                // TODO: нужно придумать что-то получше...
                $("html").html(xhr.responseText);
            };
        }
    });
};

/* Для вывода в консоль */
function testLog(text) {
    console.log(text);
};

/* Default class modification */
$.extend( $.fn.dataTableExt.oStdClasses, {
    "sSortAsc": "header headerSortDown",
    "sSortDesc": "header headerSortUp",
    "sSortable": "header"
} );

/* API method to get paging information */
$.fn.dataTableExt.oApi.fnPagingInfo = function ( oSettings ) {
    return {
        "iStart":         oSettings._iDisplayStart,
        "iEnd":           oSettings.fnDisplayEnd(),
        "iLength":        oSettings._iDisplayLength,
        "iTotal":         oSettings.fnRecordsTotal(),
        "iFilteredTotal": oSettings.fnRecordsDisplay(),
        "iPage":          Math.ceil( oSettings._iDisplayStart / oSettings._iDisplayLength ),
        "iTotalPages":    Math.ceil( oSettings.fnRecordsDisplay() / oSettings._iDisplayLength )
    };
}

/* Bootstrap style pagination control */
$.extend( $.fn.dataTableExt.oPagination, {
    "bootstrap": {
        "fnInit": function( oSettings, nPaging, fnDraw ) {
            var oLang = oSettings.oLanguage.oPaginate;
            var fnClickHandler = function ( e ) {
                e.preventDefault();
                if ( oSettings.oApi._fnPageChange(oSettings, e.data.action) ) {
                    fnDraw( oSettings );
                }
            };

            $(nPaging).addClass('pagination').append(
                '<ul>'+
                    '<li class="prev disabled"><a href="#">&larr; '+oLang.sPrevious+'</a></li>'+
                    '<li class="next disabled"><a href="#">'+oLang.sNext+' &rarr; </a></li>'+
                '</ul>'
            );
            var els = $('a', nPaging);
            $(els[0]).bind( 'click.DT', { action: "previous" }, fnClickHandler );
            $(els[1]).bind( 'click.DT', { action: "next" }, fnClickHandler );
        },

        "fnUpdate": function ( oSettings, fnDraw ) {
            var iListLength = 5;
            var oPaging = oSettings.oInstance.fnPagingInfo();
            var an = oSettings.aanFeatures.p;
            var i, j, sClass, iStart, iEnd, iHalf=Math.floor(iListLength/2);

            if ( oPaging.iTotalPages < iListLength) {
                iStart = 1;
                iEnd = oPaging.iTotalPages;
            }
            else if ( oPaging.iPage <= iHalf ) {
                iStart = 1;
                iEnd = iListLength;
            } else if ( oPaging.iPage >= (oPaging.iTotalPages-iHalf) ) {
                iStart = oPaging.iTotalPages - iListLength + 1;
                iEnd = oPaging.iTotalPages;
            } else {
                iStart = oPaging.iPage - iHalf + 1;
                iEnd = iStart + iListLength - 1;
            }

            for ( i=0, iLen=an.length ; i<iLen ; i++ ) {
                // Remove the middle elements
                $('li:gt(0)', an[i]).filter(':not(:last)').remove();

                // Add the new list items and their event handlers
                for ( j=iStart ; j<=iEnd ; j++ ) {
                    sClass = (j==oPaging.iPage+1) ? 'class="active"' : '';
                    $('<li '+sClass+'><a href="#">'+j+'</a></li>')
                        .insertBefore( $('li:last', an[i])[0] )
                        .bind('click', function (e) {
                            e.preventDefault();
                            oSettings._iDisplayStart = (parseInt($('a', this).text(),10)-1) * oPaging.iLength;
                            fnDraw( oSettings );
                        } );
                }

                // Add / remove disabled classes from the static elements
                if ( oPaging.iPage === 0 ) {
                    $('li:first', an[i]).addClass('disabled');
                } else {
                    $('li:first', an[i]).removeClass('disabled');
                }

                if ( oPaging.iPage === oPaging.iTotalPages-1 || oPaging.iTotalPages === 0 ) {
                    $('li:last', an[i]).addClass('disabled');
                } else {
                    $('li:last', an[i]).removeClass('disabled');
                }
            }
        }
    }
} );

/* Table initialisation */
function initDataTables(data) {
    table = $('table[data-model="'+data.model+'"]');
    console.log(data)
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
            $(nRow).click(function() {
                console.log(nRow)
                console.log(aData)
                var aData = oTable.fnGetData( nRow );
                console.log(aData);
                
                dblClickRow(oTable, nRow)
            });
        },
        "aoColumnDefs": data.aoColumnDefs,
        "sPaginationType": "bootstrap",
        "sDom": data.sDom || 'lfrtip',
        "bLengthChange": data.bLengthChange || true,
        "bStateSave": data.bStateSave || true,
    });
    /* Apply after */
    console.log( $($(oTable).attr('id')+'_wrapper'))
    //~ filter = $(oTable).parent().parent().find('.dataTables_filter');
    //~ filter.find('label').text('text');
    //~ console.log(filter.html())
    return false;
}

/* Добавляет вкладки на рабочую область */
function addTab() {
    model  = $(this).attr('data-model');
    func   = $(this).attr('data-func');
    object = $(this).attr('data-object');
    choice = ""
    if (model) { choice = ' data-model="'+model+'"' }
    else if (func) { choice = ' data-func="'+func+'"' }
    else if (object) { choice = ' data-object="'+object+'"' }
    
    tab_id    = $(this).attr('data-tab-id');
    tab_title = $(this).attr('data-tab-title');
    tab_text  = $(this).attr('data-tab-text');
    tab = $('#main-tab #tab-'+ tab_id)
    if (tab.length > 0) {
        // Отображаем вкладку
        tab.find('a').tab('show');
    } else {
        // Контент вкладки
        html = '<div class="tab-pane" id="tab-content-'+tab_id+'">'
            +'<div align="center"><img src="/static/img/ajax-loader.gif" /> загрузка данных...</div>'
            +'</div>'
        $('#main-tab-content').append(html);
        // Сама вкладка
        html = '<li id="tab-'+tab_id+'">'
            +'<a data-toggle="tab" href="#tab-content-'+tab_id+'"'
            + choice
            +' title="'+tab_title+'">'
            +tab_text
            +'&nbsp;<button'
            +' data-close="'+tab_id+'"'
            +' class="close">&times;</button></a></li>'
        $('#main-tab').append(html);
        // Отображаем вкладку c небольшой задержкой
        delay(function() {
            $('#main-tab a:last').tab('show');
            contentLoader($('#main-tab a:last')[0])
        }, 200);
        // Переустанавливаем биндинги на закрытие вкладок и их контента
        $('#main-tab li button.close').unbind('click').click(function() {
            close_tab_id = $(this).attr('data-close');
            $('#tab-'+close_tab_id).remove();
            $('#tab-content-'+close_tab_id).remove();
            // Удаляем из хранилища информацию об открытой вкладке
            num = $.inArray(close_tab_id, SETTINGS.values.tabs);
            if (num > -1) {
                delete SETTINGS.values.tabs[num];
                SETTINGS.cleanTabs().save();
             };
        });
        // Добавляем вкладку в хранилище, если её там нет
        // (т.к. эту же функцию использует восстановление сессии). 
        if ($.inArray(tab_id, SETTINGS.values.tabs) < 0) {
            SETTINGS.values.tabs.push(tab_id);
            SETTINGS.save();
        }
        // Устанавливаем одиночный биндинг на загрузку контента при щелчке на вкладке
        console.log(tab_id)
        a = $('#tab-'+tab_id+' a').one('click', function() {contentLoader(this)});
        console.log(a)
    }
    return true;
}

function contentLoader(obj) {
    // Загрузка контента во вкладки
    model  = $(obj).attr('data-model');
    func   = $(obj).attr('data-func');
    object = $(obj).attr('data-object');
    if (model) {
        $.getJSON('/datatables/', { model: model, info: true },
            function(data, status) {
                //~ console.log(data);
                $('#tab-content-'+data.model.replace('.', '-')).html(data.html);
                initDataTables(data);
            }
        );
    } else if (func) {
        testLog('Type is func');
    } else if (object) {
        testLog('Type is object');
    }
}

function restoreSession() {
    $.each(SETTINGS.values.tabs, function(i, item) {
        $('[data-tab-id='+item+']').trigger('click');
    });
}



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

/* Execute something after load page */
$(document).ready(function($) {
    SETTINGS.init();
    $(".dropdown-toggle").dropdown();
    $("alert").alert();
    var path = window.location.pathname;
    if (path != '/') { $('div.navbar a[href^="'+path+'"]').parents('li').addClass('active');}
    else { $('div.navbar a[href="/"]').parents('li').addClass('active');}
    $('#search').focus();
    $('#menu-app li[class!=disabled] a[data-tab-id]').click(addTab);

    restoreSession();

});
