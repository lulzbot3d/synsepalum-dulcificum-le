#ifndef INCLUDE_DULCIFICUM_GCODE_AST_ACCELERATION_H
#define INCLUDE_DULCIFICUM_GCODE_AST_ACCELERATION_H

#include "dulcificum/gcode/ast/entry.h"

#include <optional>

namespace dulcificum::gcode::ast
{
/*!
 * /brief Set the starting acceleration for moves by type.
 * P = Printing acceleration. Used for moves that include extrusion
 * T = Travel acceleration. Used for moves that include no extrusion
 */
class M204 : public Entry<R"(M204((?:\sP(?<P>\d+(?:\.\d+)?))|(?:\sT(?<T>\d+(?:\.\d+)?))|(?:\sS(?<S>\d+(?:\.\d+)?)))*$)">
{
public:
    M204() = delete;
    M204(size_t idx, std::string raw_line);
    std::optional<double> P;
    std::optional<double> T;
    std::optional<double> S;
};

/*!
 * /brief Set various motion settings.
 * X = X max jerk (units/s)
 * Y = Y max jerk (units/s)
 * Z = Z max jerk (units/s)
 * E = E max jerk (units/s)
 */
class M205 : public Entry<R"(M205((?:\sX(?<X>-?\d+(?:\.\d+)?))|(?:\sY(?<Y>-?\d+(?:\.\d+)?))|(?:\sZ(?<Z>-?\d+(?:\.\d+)?))|(?:\sE(?<E>-?\d+(?:\.\d+)?)))*$)">
{
public:
    M205() = delete;
    M205(size_t idx, std::string raw_line);
    std::optional<double> X;
    std::optional<double> Y;
    std::optional<double> Z;
    std::optional<double> E;
};

} // namespace dulcificum::gcode::ast

#endif // INCLUDE_DULCIFICUM_GCODE_AST_ACCELERATION_H