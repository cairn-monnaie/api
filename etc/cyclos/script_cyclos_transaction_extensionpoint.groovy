// TRANSACTION

import static groovyx.net.http.ContentType.*
import static groovyx.net.http.Method.*
import groovyx.net.http.HTTPBuilder

import java.util.concurrent.CountDownLatch

import org.cyclos.model.ValidationException

import org.cyclos.entities.banking.ScheduledPayment 
import org.cyclos.entities.banking.RecurringPayment 
import org.cyclos.model.banking.transactions.RecurringPaymentOccurrenceStatus 
import org.cyclos.model.banking.transactions.ScheduledPaymentInstallmentStatus 

def url = ''
def jsonBody =  []

def tx = scriptHelper.wrap(transaction)

if (! ((transaction instanceof RecurringPayment) | (transaction instanceof ScheduledPayment)) ){
    return
}

def sendWarning = false
if( transaction instanceof RecurringPayment ){
    if( tx.lastOccurrence.status == RecurringPaymentOccurrenceStatus.FAILED){
        sendWarning = true
        url = 'http://172.18.0.2:8000/operations/recurring' 
    	jsonBody =  [
            paymentID: maskId(tx.lastOccurrence.transferId), //will be null
            transactionID: maskId(tx.id),
            amount: tx.amount,
            description: tx.description,
            status: tx.lastOccurrence.status
		]           
    }
} else { // scheduled payment
    if( tx.firstInstallment.status == ScheduledPaymentInstallmentStatus.FAILED){
        sendWarning = true
        url = 'http://172.18.0.2:8000/operations/scheduled' 
    	jsonBody =  [
            paymentID: maskId(tx.firstInstallment.transferId),  //will be null
            transactionID: maskId(tx.id),
            amount: tx.amount,
            description: tx.description,
            status: tx.firstInstallment.status
		]      
        
    }
}


if (sendWarning == true){
    // Send the POST request
    def http = new HTTPBuilder(url)
    http.headers["Content-Type"] = "application/json; charset=UTF-8"
    def responseJson = null
    def responseError = []

    scriptHelper.addOnCommit {
        CountDownLatch latch = new CountDownLatch(1)
        def error = false
        http.request(POST, JSON) {
            body = jsonBody

           response.success = { resp, json ->
                responseJson = json
                latch.countDown()
            }
            response.failure = { resp ->
                responseError << resp.statusLine.statusCode
                responseError << resp.statusLine.reasonPhrase
                latch.countDown()
            }
        }
        //Await for the response
        latch.await()
        if (!responseError.empty) {
            throw new RuntimeException("Error making Cyclos sync to ${url}"
                + ", got error code ${responseError[0]}: ${responseError[1]}")
        }
        return responseJson
    }
} else {
 return   
}

// TRANSFER
import static groovyx.net.http.ContentType.*
import static groovyx.net.http.Method.*
import groovyx.net.http.HTTPBuilder

import java.util.concurrent.CountDownLatch

import org.cyclos.model.ValidationException

import org.cyclos.entities.banking.RecurringPaymentTransfer
import org.cyclos.entities.banking.ScheduledPaymentInstallmentTransfer
import org.cyclos.entities.banking.FailedPaymentOccurrence 

def url = ''
def jsonBody =  []

def tf = scriptHelper.wrap(transfer)

if (! ((transfer instanceof RecurringPaymentTransfer) | (transfer instanceof ScheduledPaymentInstallmentTransfer) | (transfer instanceof FailedPaymentOccurrence)) ){
    return
}



if( (transfer instanceof RecurringPaymentTransfer) | (transfer instanceof FailedPaymentOccurrence) ){
	url = 'http://172.18.0.2:8000/operations/recurring' 
    jsonBody =  [
        paymentID: maskId(tf.transferId),
        transactionID: maskId(tf.recurringPayment.id),
        amount: tf.amount,
        description: tf.recurringPayment.description,
        fromAccountNumber: tf.from.number,
        toAccountNumber: tf.to.number,
        status: tf.status
	]    

} else {
	url = 'http://172.18.0.2:8000/operations/scheduled'
    jsonBody =  [
        paymentID: maskId(tf.installment.transferId),
        transactionID: maskId(tf.transactionId),
        amount: tf.amount,
        description: tf.transaction.description,
        fromAccountNumber: tf.from.number,
        toAccountNumber: tf.to.number,
        status: tf.installment.status
	]
}


// Send the POST request
def http = new HTTPBuilder(url)
http.headers["Content-Type"] = "application/json; charset=UTF-8"
def responseJson = null
def responseError = []

scriptHelper.addOnCommit {
    CountDownLatch latch = new CountDownLatch(1)
    def error = false
    http.request(POST, JSON) {
        body = jsonBody
        
       response.success = { resp, json ->
        	responseJson = json
        	latch.countDown()
        }
        response.failure = { resp ->
        	responseError << resp.statusLine.statusCode
        	responseError << resp.statusLine.reasonPhrase
        	latch.countDown()
        }
    }
    //Await for the response
	latch.await()
	if (!responseError.empty) {
		throw new RuntimeException("Error making Cyclos sync to ${url}"
			+ ", got error code ${responseError[0]}: ${responseError[1]}")
	}
	return responseJson
}

