/**
 * jQuery dateParser plugin 0.2
 *
 * @author Grigoriy Kramaranko, 2014
 * @license GNU General Public License 3 <http://www.gnu.org/licenses/>
 * 
 */

(function ($) {
    var pluginName="dateParser";

    /* Парсер времени в ISO8601 (с разделителями), ECMA-262 и naive datetime.
     * Обязательным параметром является `string`. Поддерживаются:
     *      "2013-12-31"
     *      "2013-12-31 23:59"
     *      "2013-12-31 23:59Z"
     *      "2013-12-31 23:59+00:00"
     *      "2013-12-31 23:59:59"
     *      "2013-12-31 23:59:59Z"
     *      "2013-12-31 23:59:59+00:00"
     *      "2013-12-31 23:59:59.999"
     *      "2013-12-31 23:59:59.999Z"
     *      "2013-12-31 23:59:59.999+00:00"
     * Разделитель даты от времени: пробел или `T`
     * 
     * В области видимости может быть установлена статическая переменная
     * window.SERVER_TZ_OFFSET, равная количеству минут от Гринвича *-1,
     * так как это задаётся в JavaScript: (new Date()).getTimezoneOffset().
     * То есть для Москвы это будет -240, для Вашингтона +300.
     * 
     * Если этой переменной нет и не передан третий параметр
     * (с кол-вом минут), либо в функцию передан второй параметр как
     * истина, то простое время (naive) идентифицируется как локальное время.
     * 
     * В остальных случаях простое время идентифицируется как время сервера.
     * 
     * Examples (browser location in GMT+11):
     * 
     * // Server location in UTC
     * 
     * >> window.SERVER_TZ_OFFSET = 0  
     * >> $.dateParser('2014-01-01 00:00:00')
     * Wed Jan 01 2014 11:00:00 GMT+1100 (VLAT)
     * >> $.dateParser('2014-01-01 00:00:00', true)   // on Vladivostok
     * Wed Jan 01 2014 00:00:00 GMT+1100 (VLAT)
     * >> $.dateParser('2014-01-01 00:00:00', null, -240)  // on Moscow
     * Wed Jan 01 2014 07:00:00 GMT+1100 (VLAT)
     * 
     * // Server location in Vladivostok
     * 
     * >> window.SERVER_TZ_OFFSET = -660
     * >> $.dateParser('2014-01-01 00:00:00')
     * Wed Jan 01 2014 00:00:00 GMT+1100 (VLAT)
     * >> $.dateParser('2014-01-01 00:00:00', true)   // on Vladivostok
     * Wed Jan 01 2014 00:00:00 GMT+1100 (VLAT)
     * >> $.dateParser('2014-01-01 00:00:00', null, -240)  // on Moscow
     * Wed Jan 01 2014 07:00:00 GMT+1100 (VLAT)
     * 
     * >> $.dateParser('2014-01-01T00:00:00Z')
     * Wed Jan 01 2014 11:00:00 GMT+1100 (VLAT)
     * >> $.dateParser('2014-01-01T00:00:00+03:00')
     * Wed Jan 01 2014 08:00:00 GMT+1100 (VLAT)
     * 
     */
    $[pluginName] = function(string, local, custom_tz_offset) {
        var pre = $[pluginName].preParser(string);
        if (!pre) return null;

        var localoffset = (new Date()).getTimezoneOffset(),
            tzoffset = 0, minute=pre.minute, date = null;

        if (minute != null) {
            if (custom_tz_offset === undefined) {
                var custom_tz_offset = window.SERVER_TZ_OFFSET || 0;
            }
            if (pre.UTC) {
                minute -= localoffset;
            } else if (pre.TZhour != null || pre.TZminute != null) {
                tzoffset = pre.TZsign * (pre.TZhour * 60  + pre.TZminute) * -1;
                minute -= localoffset - tzoffset;
            } else if (!local) {
                minute -= localoffset - custom_tz_offset;
            }
        }

        date = new Date(pre.year, (pre.month ? (pre.month - 1) : 0), pre.day,
                        pre.hour, minute, pre.second, pre.millisecond);

        if (minute == null) {
            date.without_time = true;
        }

        return date
    };

    /* Первичный парсер. */
    $[pluginName].preParser = function(string) {
        var re = /^(\d{4}|[+\-]\d{6})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{3}))?)?(?:(Z)|([+\-])(\d{2})(?::(\d{2}))?)?)?$/,
            L = re.exec(string);
        if (!L) return null;

        return {
            'year': Number(L[1]),
            'month': Number(L[2]),
            'day': Number(L[3]),
            'hour': L[4] ? Number(L[4]) : null,
            'minute': L[5] ? Number(L[5]) : null,
            'second': L[6] ? Number(L[6]) : null,
            'millisecond': L[7] ? Number(L[7]) : null,
            'UTC': L[8] ? true : false,
            'TZsign': (L[9] == '-') ? -1 : 1,
            'TZhour': L[10] ? Number(L[10]) : null,
            'TZminute': L[11] ? Number(L[11]) : null,
        };
    };

/*
    $[pluginName].test = function() {
        var fn = $[pluginName],
            val = [
                '2013-12-31',
                '2013-12-31 23:59',
                '2013-12-31 23:59Z',
                '2013-12-31 23:59+10:00',
                '2013-12-31 23:59-10:00',
                '2013-12-31 23:59:59',
                '2013-12-31 23:59:59Z',
                '2013-12-31 23:59:59+10:00',
                '2013-12-31 23:59:59-10:00',
                '2013-12-31 23:59:59.999',
                '2013-12-31 23:59:59.999Z',
                '2013-12-31 23:59:59.999+10:00',
                '2013-12-31 23:59:59.999-10:00',

                '2013-12-31T23:59',
                '2013-12-31T23:59Z',
                '2013-12-31T23:59+10:00',
                '2013-12-31T23:59-10:00',
                '2013-12-31T23:59:59',
                '2013-12-31T23:59:59Z',
                '2013-12-31T23:59:59+10:00',
                '2013-12-31T23:59:59-10:00',
                '2013-12-31T23:59:59.999',
                '2013-12-31T23:59:59.999Z',
                '2013-12-31T23:59:59.999+10:00',
                '2013-12-31T23:59:59.999-10:00',

                '-202013-12-31',
                '-202013-12-31 23:59',
                '-202013-12-31 23:59Z',
                '-202013-12-31 23:59+10:00',
                '-202013-12-31 23:59-10:00',
                '-202013-12-31 23:59:59',
                '-202013-12-31 23:59:59Z',
                '-202013-12-31 23:59:59+10:00',
                '-202013-12-31 23:59:59-10:00',
                '-202013-12-31 23:59:59.999',
                '-202013-12-31 23:59:59.999Z',
                '-202013-12-31 23:59:59.999+10:00',
                '-202013-12-31 23:59:59.999-10:00',
            ];
        $.each(val, function(i, it) {console.log(fn(it), 'from ' + it)});
        return true;
    }
*/

}(jQuery));
