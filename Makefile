run:
	python -m receipt_app.main receipts --print

expenses:
	python -m receipt_app.main receipts --expenses 2019-01-01 2026-12-31

plot:
	python -m receipt_app.main receipts --plot
