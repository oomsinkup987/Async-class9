# Washing machine state

## START
topic:v1cdti/app/get/6310301025/model-01/sn-01
payload: {
    "action"    :   "get",
    "project"   :   "6310301025",
    "model"     :   "model-01",
    "serial"    :   "sn-01",
    "name"      :   "START",
    "value"     :   "START"
}

## READY
topic:v1cdti/app/get/6310301025/model-01/sn-01
payload: {
    "action"    :   "get",
    "project"   :   "6310301025",
    "model"     :   "model-01",
    "serial"    :   "sn-01",
    "name"      :   "STATUS",
    "value"     :   "READY"
}


## FILLWATER
topic:v1cdti/app/set/6310301025/model-01/sn-01
payload: {
    "action"    :   "get",
    "project"   :   "6310301025",
    "model"     :   "model-01",
    "serial"    :   "sn-01",
    "name"      :   "STATUS",
    "value"     :   "FILLWATER_ON"
}

## HEATWATER
topic:v1cdti/app/set/6310301025/model-01/sn-01
payload: {
    "action"    :   "set",
    "project"   :   "6310301025",
    "model"     :   "model-01",
    "serial"    :   "sn-01",
    "name"      :   "STATUS",
    "value"     :   "HEATWATER_ON"
}

## WASH
topic:v1cdti/app/get/6310301025/model-01/sn-01
payload: {
    "action"    :   "get",
    "project"   :   "6310301025",
    "model"     :   "model-01",
    "serial"    :   "sn-01",
    "name"      :   "STATUS",
    "value"     :   "WASH_ON"
}

## RINSE
topic:v1cdti/app/get/6310301025/model-01/sn-01
payload: {
    "action"    :   "get",
    "project"   :   "6310301025",
    "model"     :   "model-01",
    "serial"    :   "sn-01",
    "name"      :   "STATUS",
    "value"     :   "RINSE_ON"
}

## SPIN
topic:v1cdti/app/get/6310301025/model-01/sn-01
payload: {
    "action"    :   "get",
    "project"   :   "6310301025",
    "model"     :   "model-01",
    "serial"    :   "sn-01",
    "name"      :   "STATUS",
    "value"     :   "SPIN_ON"
}

# Operation state

## DOORCLOSE
topic:v1cdti/app/get/6310301025/model-01/sn-01
payload: {
    "action"    :   "get",
    "project"   :   "6310301025",
    "model"     :   "model-01",
    "serial"    :   "sn-01",
    "name"      :   "OP_STATUS_DOORCLOSE",
    "value"     :   "DOORCLOSE"
}

## WATERFULLLEVEL
topic:v1cdti/app/get/6310301025/model-01/sn-01
payload: {
    "action"    :   "get",
    "project"   :   "6310301025",
    "model"     :   "model-01",
    "serial"    :   "sn-01",
    "name"      :   "OP_STATUS_WATERFULLLEVEL",
    "value"     :   "WATERFULLLEVEL"
}

## TEMPERATUREREACHED
topic:v1cdti/app/set/6310301025/model-01/sn-01
payload: {
    "action"    :   "set",
    "project"   :   "6310301025",
    "model"     :   "model-01",
    "serial"    :   "sn-01",
    "name"      :   "OP_STATUS_TEMPERATUREREACHED",
    "value"     :   "TEMPERATUREREACHED"
}


# FAULT state

## TIMEOUT
topic:v1cdti/app/get/6310301025/model-01/sn-01
payload: {
    "action"    :   "get",
    "project"   :   "6310301014",
    "model"     :   "model-01",
    "serial"    :   "sn-01",
    "name"      :   "FAULT_STATUS_TIMEOUT",
    "value"     :   "TIMEOUT"
}

## OUTOFBALANCE
topic:v1cdti/app/set/6310301025/model-01/sn-01
payload: {
    "action"    :   "set",
    "project"   :   "6310301025",
    "model"     :   "model-01",
    "serial"    :   "sn-01",
    "name"      :   "FAULT_STATUS_OUTOFBALANCE",
    "value"     :   "OUTOFBALANCE"
}

## MOTORFAILURE
topic:v1cdti/app/set/6310301025/model-01/sn-01
payload: {
    "action"    :   "set",
    "project"   :   "6310301025",
    "model"     :   "model-01",
    "serial"    :   "sn-01",
    "name"      :   "FAULT_STATUS_MOTORFAILURE",
    "value"     :   "FAULT"
}

## FAULTCLEARED
topic:v1cdti/app/set/6310301025/model-01/sn-01
payload: {
    "action"    :   "set",
    "project"   :   "6310301025",
    "model"     :   "model-01",
    "serial"    :   "sn-01",
    "name"      :   "FAULT_STATUS_FAULTCLEARED",
    "value"     :   "FAULTCLEARED"
}