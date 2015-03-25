# Copyright 2014 Cloudera Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from ibis.expr.tests.mocks import MockConnection
import ibis.expr.api as api
import ibis.expr.operations as ops
import ibis.expr.types as ir


class TestBuiltins(unittest.TestCase):

    def setUp(self):
        self.con = MockConnection()
        self.alltypes = self.con.table('functional_alltypes')
        self.lineitem = self.con.table('tpch_lineitem')

    def test_abs(self):
        colnames = ['tinyint_col', 'smallint_col', 'int_col', 'bigint_col',
                    'float_col', 'double_col']

        fname = 'abs'
        op = ops.Abs

        for col in colnames:
            expr = self.alltypes[col]
            self._check_unary_op(expr, fname, op, type(expr))

        expr = self.lineitem.l_extendedprice
        self._check_unary_op(expr, fname, op, type(expr))

    def test_zeroifnull(self):
        dresult = self.alltypes.double_col.zeroifnull()
        iresult = self.alltypes.int_col.zeroifnull()

        assert type(dresult.op()) == ops.ZeroIfNull
        assert type(dresult) == ir.DoubleArray

        # Impala upconverts all ints to bigint. Hmm.
        assert type(iresult) == ir.Int64Array

    def test_fillna(self):
        result = self.alltypes.double_col.fillna(5)
        assert isinstance(result, ir.DoubleArray)

        expected = (self.alltypes.double_col.isnull()
                    .ifelse(5, self.alltypes.double_col))
        assert result.equals(expected)

        result = self.alltypes.bool_col.fillna(True)
        assert isinstance(result, ir.BooleanArray)

        result = self.alltypes.int_col.fillna(self.alltypes.bigint_col)
        assert isinstance(result, ir.Int64Array)

    def test_ceil_floor(self):
        cresult = self.alltypes.double_col.ceil()
        fresult = self.alltypes.double_col.floor()
        assert isinstance(cresult, ir.Int32Array)
        assert isinstance(fresult, ir.Int32Array)
        assert type(cresult.op()) == ops.Ceil
        assert type(fresult.op()) == ops.Floor

        cresult = api.literal(1.2345).ceil()
        fresult = api.literal(1.2345).floor()
        assert isinstance(cresult, ir.Int32Scalar)
        assert isinstance(fresult, ir.Int32Scalar)

        dec_col = self.lineitem.l_extendedprice
        cresult = dec_col.ceil()
        fresult = dec_col.floor()
        assert isinstance(cresult, ir.DecimalArray)
        assert cresult.meta == dec_col.meta

        assert isinstance(fresult, ir.DecimalArray)
        assert fresult.meta == dec_col.meta

    def test_sign(self):
        result = self.alltypes.double_col.sign()
        assert isinstance(result, ir.Int32Array)
        assert type(result.op()) == ops.Sign

        result = api.literal(1.2345).sign()
        assert isinstance(result, ir.Int32Scalar)

        dec_col = self.lineitem.l_extendedprice
        result = dec_col.sign()
        assert isinstance(result, ir.Int32Array)

    def test_round(self):
        result = self.alltypes.double_col.round()
        assert isinstance(result, ir.Int64Array)
        assert result.op().digits is None

        result = self.alltypes.double_col.round(2)
        assert isinstance(result, ir.DoubleArray)
        assert result.op().digits == 2

        # Even integers are double (at least in Impala, check with other DB
        # implementations)
        result = self.alltypes.int_col.round(2)
        assert isinstance(result, ir.DoubleArray)

        dec = self.lineitem.l_extendedprice
        result = dec.round()
        assert isinstance(result, ir.DecimalArray)

        result = dec.round(2)
        assert isinstance(result, ir.DecimalArray)

        result = api.literal(1.2345).round()
        assert isinstance(result, ir.Int64Scalar)

    def _check_unary_op(self, expr, fname, ex_op, ex_type):
        result = getattr(expr, fname)()
        assert type(result.op()) == ex_op
        assert type(result) == ex_type