


class DataStorage {
 constructor() {
  this.storage = {}
 }
 save_data = (key, data) => {
  if (!(key in this.storage)) {
   this.storage[key] = null
  }
  this.storage[key] = data
 }

 get_data = (key, pathtovalue) => {
  if (!(key in this.storage)) {
   return null
  }
  if (!pathtovalue) return this.storage[key]
  let tmp = Object.assign({}, this.storage[key])
  let subkeys = pathtovalue.split('.')
  for (let i in subkeys) {
   tmp = tmp[subkeys[i]]
  }
  return tmp
 }

}

export let dataController = new DataStorage()
