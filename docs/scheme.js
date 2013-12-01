// Описание схемы сайта, получаемой методом get_scheme в API
//~ DEFAULT_PERMISSIONS = { 'create': false, 'read': true, 'update': false, 'delete': false }

SCHEME = {
    icon: null,
    label: 'Бизон', 
    dashboard: [],
    reports: {},
    apps_list: ['tests'],
    apps: {
        tests: {
            icon: null,
            label: 'Тесты',
            models_list: ['secondmodel', 'firstmodel'],
            models: {
                firstmodel: {
                    icon: null,
                    label: 'Товары',
                    has_cloning: false,
                    has_coping: false,
                    per_page: 10,
                    per_page_min: 5,
                    per_page_max: 100,
                    permissions: {
                        'create': true, 'read': true, 'update': true,
                        'delete': true, 'other': false},
                    fields: {
                        // Пример PrimaryKey и описание возможных атрибутов
                        // прочих полей
                        'id': {
                            'label': 'ID', // название поля
                            'type': 'int', // возможные типы:
                                           // int, int_list, float, decimal,
                                           // str, password, text, email, url, path,
                                           // html, markdown,
                                           // datetime, date, time, timedelta
                                           // file, image, bool, null_bool,
                                           // select, object, object_list
                            // необязательные поля:
                            'disabled': true, // общий режим редактирования
                            'not_upgrade': false, // не обновлять поле сохранённого объекта 
                            'hidden': true, // скрытое поле
                            'required': false, // обязательно к заполнению
                            'default': null, // значение по-умолчанию,
                                             // для дат это количество
                                             // секунд от текущего времени
                            'placeholder': null, // заполнитель поля
                            'help': null, // подсказка
                            'options': null, // для выбора из жесткого списка
                            'min': null, // минимальное значение
                            'max': null, // максимальное значение
                            'format': null, // формат вывода на экран
                                            // regexp, словарь или строка
                            'round': null,  // если == null, то не производить
                                            // округление, или указать разряд
                        },
                        'created': {
                            'label': 'Дата создания',
                            'type': 'datetime',
                            'disabled': true,
                            'format': null, // выведет согласно настроек
                                            // клиентского приложения
                                            // (необязательно к указанию)
                        },
                        'is_active': {
                            'label': 'Активно',
                            'type': 'bool',
                            'required': true,
                            'default': true,
                        },
                        'title': {
                            'label': 'Название',
                            'type': 'str',
                            'default': 'Название объекта',
                            'placeholder': 'Введите название',
                            'help': 'Не менее 1 символа, но не более 255',
                            'min': 1,
                            'max': 255,
                        },
                        'count': {
                            'label': 'Количество',
                            'type': 'decimal', // возможны float значения
                            'required': true,
                            'default': '1',
                            'placeholder': 'Введите количество',
                            'help': 'Не менее 1 символа, но не более 50',
                            'min': 1,
                            'max': 50,
                            'format': {'max_digits':10, 'decimal_places':2, 'separator':','}, 
                        },
                        'file': {
                            'label': 'Файл',
                            'type': "file",
                            'required': true,
                            'placeholder': 'Выберите файл для загрузки',
                            'help': 'Не более 5 мегабайт',
                            'min': 1,
                            'max': 5242880, // в байтах
                        },
                        'forein_key': {
                            'label': 'Внешняя модель',
                            'type': "object",
                            'required': true,
                            'placeholder': 'Выберите объект',
                        },
                        'many_to_many': {
                            'label': 'Другая внешняя модель',
                            'type': "list",
                            'required': true,
                            'placeholder': 'Выберите объект',
                        },
                        'select': {
                            'label': 'Простой выбор',
                            'type': "select",
                            'required': false,
                            'placeholder': 'Выберите объект',
                            'options': [
                                ['value1', 'display string 1'],
                                ['value2', 'display string 2'],
                            ],
                        },
                    },
                    fields_set: [
                        {
                            'label': 'Обязательные поля',
                            'fields':[
                                'is_active', 'title', 'count',
                            ],
                        },
                        'forein_key', 'many_to_many',
                        ['created', 'file'],
                    ],
                    fields_search: ['title'],
                    column_default: '__unicode__', // либо ['title', 'summa', ...]
                    columns: [
                        {'name': null, 'label': 'объект', 'ordering': false, 'order_by': null},
                        {'name': 'is_active', 'label': 'активно', 'ordering': true, 'order_by': 'ASC'},
                        {'name': 'select', 'label': 'пр.выбор', 'ordering': true, 'order_by': null},
                        {'name': 'property_or_method', 'label': 'Свойство', 'ordering': false, 'order_by': null},
                        {'name': 'id', 'label': 'ID', 'ordering': true, 'order_by': 'DESC'},
                    ],
                    rows_rules: {
                        'is_active': {
                            'is_null': {'value': true, 'class': 'muted'},
                            'eq': {'value': false, 'class': 'danger'},
                        },
                        'created': {
                            'lt': {'value': '2013-10-10', 'class': 'muted'}, // парсинг даты
                            'eq': {'value': null, 'class': 'class_X'}, // null == new Date()
                            'gt': {'value': -3600, 'class': 'class_X'}, // new Date() - 3600 секунд
                            'range': {'value': ['2013-10-10', '2013-12-31'], 'class': 'class_X'}, 
                        },
                    },
                    rows_rules_list: ['is_active', 'created'],
                    actions: {
                        'delete': {'label': 'Удалить выбранные', 'confirm': true},
                        'set_active': {'label': 'Сделать активными', 'confirm': false},
                        'set_nonactive': {'label': 'Сделать неактивными', 'confirm': false},
                    },
                    actions_list: ['delete', 'set_active', 'set_nonactive'],
                    filters: {},
                    filters_list: [],
                    compositions: {
                        'secondmodel_set': {
                            icon: null,
                            label: 'Композиция второй модели',
                            app_name: 'tests',
                            model_name: 'secondmodel',
                            has_cloning: true,
                            has_coping: true,
                            per_page: 10,
                            per_page_min: 5,
                            per_page_max: 100,
                            permissions: {
                                'create': true, 'read': true, 'update': true,
                                'delete': true, 'other': false},
                            fields: {
                                'id': {
                                    'label': 'ID',
                                    'type': 'int',
                                },
                                'title': {
                                    'label': 'Название',
                                    'type': 'str',
                                    'default': 'Название объекта',
                                    'placeholder': 'Введите название',
                                    'help': 'Не менее 1 символа, но не более 255',
                                    'min': 1,
                                    'max': 255,
                                },
                                'forein_key': {
                                    'label': 'Первая модель',
                                    'type': "object",
                                    'hidden': true,
                                },
                            },
                            fields_set: null,
                            fields_search: ['title'],
                            column_default: '__unicode__',
                            columns: [
                                {'name': null, 'label': 'объект', 'ordering': false, 'order_by': null},
                                {'name': 'property_or_method', 'label': 'Свойство', 'ordering': false, 'order_by': null},
                                {'name': 'id', 'label': 'ID', 'ordering': true, 'order_by': 'DESC'},
                            ],
                            rows_rules: null,
                            rows_rules_list: null,
                            actions: {
                                'delete': {'label': 'Удалить выбранные', 'confirm': true},
                            },
                            actions_list: ['delete'],
                            model_reports: [['model_report1', 'Отчёт №1'], ['model_report2', 'Отчёт №2']],
                            object_reports: [['object_report1', 'Отчёт №1'], ['object_report2', 'Отчёт №2']],
                            summary: [
                                {'name': 'total_summa', 'label': 'Итого'},
                            ],
                        },
                    },
                    compositions_list: ['secondmodel_set'],
                    model_reports: [['model_report1', 'Отчёт №1'], ['model_report2', 'Отчёт №2']],
                    object_reports: [['object_report1', 'Отчёт №1'], ['object_report2', 'Отчёт №2']],
                    summary: [
                        {'name': 'total_summa', 'label': 'Итого'},
                    ],
                },
            },
        },
    }
    settings: {},
}

data = [
    {'__unicode__': 'Товар1', 'is_active': true, 'select': 'value1', 'property_or_method': 1000, 'id': 1},
    {'__unicode__': 'Товар2', 'is_active': true, 'select': 'value1', 'property_or_method': 1001, 'id': 2},
    {'__unicode__': 'Товар3', 'is_active': false, 'select': 'value2', 'property_or_method': 1002, 'id': 3},
    {'__unicode__': 'Товар4', 'is_active': true, 'select': 'value1', 'property_or_method': 1003, 'id': 4},
    {'__unicode__': 'Товар5', 'is_active': true, 'select': 'value1', 'property_or_method': 1004, 'id': 5},
]

fields  = SCHEME.apps.tests.models.firstmodel.fields;
columns = SCHEME.apps.tests.models.firstmodel.columns;

function htmlField(fields, column, data) {
    var html = '';
    
    
    
    return html;
}



