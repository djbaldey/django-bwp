-- Триггерная процедура запуска пересчёта при добавлении позиции

CREATE OR REPLACE FUNCTION warehouses_stock_tfunc_after_insert_or_delete()
  RETURNS trigger AS
$BODY$
DECLARE
    INCOMING   CONSTANT char := '+';
    OUTCOMING  CONSTANT char := '-';
    MOVING_OUT CONSTANT char := '<';
    MOVING_IN  CONSTANT char := '>';
    INVENTORY  CONSTANT char := '=';
    warehouse_dst       int;
    post_stock          record;
    OBJ                 record;

    _count real := 0.0;
    _price real := 0.0;
    _summa real := 0.0;
    _diff  real := 0.0;

BEGIN
    -- test
    RAISE DEBUG 'run % as %', TG_NAME, TG_OP;

    IF TG_OP = 'DELETE' THEN
        OBJ := OLD;
        -- Получить предыдущую строку остатков и заблокировать её
        SELECT i.count, i.price, i.summa INTO _count, _price, _summa FROM warehouses_stock i
            WHERE
                i.nomenclature_id = OBJ.nomenclature_id
                AND i.warehouse_id = OBJ.warehouse_id
                AND i.id != OBJ.id
                AND (i.date_time < OBJ.date_time OR (i.date_time = OBJ.date_time AND i.id < OBJ.id))
            ORDER BY i.date_time DESC, i.id DESC
            LIMIT 1 FOR UPDATE;
        IF NOT FOUND THEN
            _count := 0.0;
            _price := 0.0;
            _summa := 0.0;
        END IF;
    ELSE
        OBJ    := NEW;
        _count := OBJ.count;
        _price := OBJ.price;
        _summa := OBJ.summa;
    END IF;


    --*-- ОБНОВЛЕНИЕ ПОСЛЕДУЮЩИХ --*--

    -- Заблокировать все последующие строки
    FOR post_stock IN SELECT * FROM warehouses_stock
        WHERE
            nomenclature_id = OBJ.nomenclature_id
            AND warehouse_id = OBJ.warehouse_id
            AND (date_time > OBJ.date_time OR (date_time = OBJ.date_time AND id < OBJ.id))
            AND id != OBJ.id
        ORDER BY date_time, id
        FOR UPDATE
    LOOP
        IF post_stock.kind = INVENTORY THEN
            _diff  := post_stock.doc_count - _count;
            _count := post_stock.doc_count;
            _price := _price;
            _summa := _count*_price;
            UPDATE warehouses_stock
               SET doc_count=_count, count=_count,
                   doc_price=_price, price=_price,
                   doc_summa=_summa, summa=_summa,
                   diff=_diff, diff_summa=_diff*_price,
                   _trigger_lock=TRUE
             WHERE id = post_stock.id;
        ELSIF post_stock.kind IN (OUTCOMING, MOVING_OUT) THEN
            _count := _count - post_stock.doc_count;
            _price := _price;
            _summa := _count*_price;
            UPDATE warehouses_stock
               SET doc_summa=post_stock.doc_count*_price,
                   doc_price=_price,
                   count=_count,
                   price=_price,
                   summa=_summa,
                   _trigger_lock=TRUE
             WHERE id = post_stock.id;
        ELSIF post_stock.kind IN (INCOMING, MOVING_IN) THEN
            _count := _count + post_stock.doc_count;
            -- если остаток больше нуля,
            -- то установить усреднённую цену остатков
            IF _count > 0 and _summa > 0 THEN
                _price := 1.0 * (post_stock.doc_summa + _summa) / _count;
            ELSE
                _price := post_stock.doc_price;
                -- TODO: наверное сделать поле для извещения
                -- пользователя о том, что остатки и цены отрицательные
            END IF;
            _summa := _count*_price;
            UPDATE warehouses_stock
               SET count=_count,
                   price=_price,
                   summa=_summa,
                   _trigger_lock=TRUE
             WHERE id = post_stock.id;
        END IF;

    END LOOP;


    -- ЗАПУСК ВЫЧИСЛЕНИЙ ПО СКЛАДУ НАЗНАЧЕНИЯ --

    -- Если это перемещение со склада, то вставить/удалить
    -- строку перемещения на другом складе, инициируя рекурсивное
    -- обновление по другому складу.
    IF OBJ.kind = MOVING_OUT THEN
        IF TG_OP = 'DELETE' THEN
            DELETE FROM warehouses_stock WHERE parent_id = OBJ.id;
        ELSE
            -- Получить склад назначения из документа
            SELECT d.warehouse_id INTO warehouse_dst
            FROM warehouses_document d
            WHERE d.id = OBJ.document_id;

            INSERT INTO warehouses_stock 
                (created, updated, date_time,
                warehouse_id, nomenclature_id, kind, parent_id,
                doc_price, doc_count, doc_summa,
                document_id)
            VALUES
                (OBJ.created, OBJ.updated, OBJ.date_time,
                warehouse_dst, OBJ.nomenclature_id, MOVING_IN, OBJ.id,
                OBJ.doc_price, OBJ.doc_count, OBJ.doc_summa,
                OBJ.document_id);
        END IF;
    END IF;

    RETURN OBJ;
END;
$BODY$
LANGUAGE 'plpgsql';

-- DROP TRIGGER warehouses_stock_after_insert_or_delete ON warehouses_stock;
CREATE TRIGGER warehouses_stock_after_insert_or_delete
    AFTER INSERT OR DELETE
    ON warehouses_stock
    FOR EACH ROW
    EXECUTE PROCEDURE warehouses_stock_tfunc_after_insert_or_delete();

