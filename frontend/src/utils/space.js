import { SpaceTypes } from './enums'

export const isDiscrete = space => space === SpaceTypes.DISCRETE
export const isBox = space => space === SpaceTypes.BOX
export const isMultiDiscrete = space => space === SpaceTypes.MULTI_DISCRETE
export const isDict = space => space === SpaceTypes.DICT
