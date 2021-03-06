import sys
from routes import Routes


def debug(message):
    sys.stderr.write(message + "\n")


class Logic:
    def __init__(self, lnd, remote_pubkey, amount):
        self.lnd = lnd
        self.remote_pubkey = remote_pubkey
        self.amount = amount

    def rebalance(self):
        debug("Sending %d satoshis to rebalance, remote pubkey: %s" %
              (self.amount, self.remote_pubkey))

        payment_request = self.generate_invoice()
        routes = Routes(self.lnd, payment_request, self.remote_pubkey)

        if not routes.has_next():
            debug("Could not find any suitable route")
            return None

        counter = 0
        while routes.has_next():
            counter += 1
            debug("Trying route #%d" % counter)

            route = routes.get_next()
            response = self.lnd.send_payment(payment_request, [route])
            is_successful = response.payment_error == ""

            if is_successful:
                fees_msat = response.payment_route.total_fees_msat
                fees_satoshi = round(float(fees_msat) / 1000.0, 3)
                debug("Success! Paid %d Satoshi in fees" % fees_satoshi)
                return response
            elif "TemporaryChannelFailure" in response.payment_error:
                debug("TemporaryChannelFailure (not enough funds along the route?)")
            else:
                debug("Error: %s" % response.payment_error)
        return None

    def generate_invoice(self):
        memo = "Rebalance of channel to " + self.remote_pubkey
        return self.lnd.generate_invoice(memo, self.amount)
