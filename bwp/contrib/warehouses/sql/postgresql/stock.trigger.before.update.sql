-- Триггерная процедура партиционирования при обновлении

CREATE OR REPLACE FUNCTION warehouses_stock_tfunc_before_update()
  RETURNS trigger AS
$BODY$
DECLARE
    INCOMING   CONSTANT char := '+';
    MOVING_OUT CONSTANT char := '<';
    MOVING_IN  CONSTANT char := '>';
BEGIN
    -- test
    RAISE DEBUG 'run %', TG_NAME;

    IF NEW._trigger_lock = TRUE THEN
        NEW._trigger_lock := FALSE;
        RETURN NEW;
    END IF;

    IF OLD.kind = MOVING_OUT THEN
        DELETE FROM warehouses_stock WHERE parent_id = OLD.id;
    END IF;

    DELETE FROM warehouses_stock WHERE id = OLD.id;

    -- При обновлении сбрасываем цену для прихода, так как приоритет у суммы
    IF NEW.kind = INCOMING AND NOT NEW.doc_summa IS NULL AND
        (OLD.doc_summa != NEW.doc_summa OR OLD.doc_price = NEW.doc_price)
    THEN
        NEW.doc_price := NULL;
    END IF;

    INSERT INTO warehouses_stock VALUES (NEW.*);

    RETURN NULL;
END;
$BODY$
LANGUAGE 'plpgsql';

-- DROP TRIGGER warehouses_stock_before_update ON warehouses_stock;
CREATE TRIGGER warehouses_stock_before_update
    BEFORE UPDATE
    ON warehouses_stock
    FOR EACH ROW
    EXECUTE PROCEDURE warehouses_stock_tfunc_before_update();

